import os
import json
import re
from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from core.prompts import STORY_PROMPT
from models.story import Story, StoryNode
from core.models import StoryLLMResponse, StoryNodeLLM
from dotenv import load_dotenv

load_dotenv()


class StoryGenerator:

    @classmethod
    def _get_llm(cls):
        serviceurl = os.getenv("CHOREO_OPENAI_CONNECTION_SERVICEURL")
        consumerkey = os.getenv("CHOREO_OPENAI_CONNECTION_CONSUMERKEY")

        if serviceurl and consumerkey:
            return ChatOpenAI(
                model="gpt-3.5-turbo",
                openai_api_base=f"{serviceurl}/v1",
                openai_api_key=consumerkey,
                temperature=0.7,  # Added temperature for better creativity
            )

        return ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)

    @classmethod
    def generate_story(cls, db: Session, session_id: str, theme: str = "fantasy") -> Story:
        llm = cls._get_llm()
        story_parser = PydanticOutputParser(pydantic_object=StoryLLMResponse)

        # 1. Improved prompt: explicitly telling the AI to avoid schema repetition
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", STORY_PROMPT),
                (
                    "human",
                    "Generate a complete adventure story based on the theme: {theme}. \n{format_instructions}",
                ),
            ]
        )

        # 2. Format the prompt correctly with input variables
        formatted_prompt = prompt.format_prompt(
            theme=theme, format_instructions=story_parser.get_format_instructions()
        )

        raw_response = llm.invoke(formatted_prompt.to_messages())

        # 3. Clean the response (Crucial Step)
        response_text = (
            raw_response.content if hasattr(raw_response, "content") else str(raw_response)
        )

        # This regex removes Markdown JSON blocks if present
        if "```json" in response_text:
            response_text = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL).group(1)
        elif "```" in response_text:
            response_text = re.search(r"```\s*(.*?)\s*```", response_text, re.DOTALL).group(1)

        response_text = response_text.strip()

        # 4. Parse the cleaned text
        try:
            story_structure = story_parser.parse(response_text)
        except Exception as e:
            # Fallback: if parsing fails, print the text to logs so you can see what the AI did
            print(f"DEBUG: Failed to parse. Raw content: {response_text}")
            raise ValueError(f"AI returned invalid JSON: {str(e)}")

        # 5. DB Persistence
        story_db = Story(title=story_structure.title, session_id=session_id)
        db.add(story_db)
        db.flush()

        # Process the nested nodes
        cls._process_story_node(db, story_db.id, story_structure.rootNode, is_root=True)

        db.commit()
        return story_db

    @classmethod
    def _process_story_node(
        cls, db: Session, story_id: int, node_data: StoryNodeLLM, is_root: bool = False
    ) -> StoryNode:
        # Use getattr or model_dump to handle Pydantic objects safely
        content = node_data.content
        is_ending = node_data.isEnding
        is_winning_ending = node_data.isWinningEnding

        node = StoryNode(
            story_id=story_id,
            content=content,
            is_root=is_root,
            is_ending=is_ending,
            is_winning_ending=is_winning_ending,
            options=[],
        )
        db.add(node)
        db.flush()

        if not is_ending and node_data.options:
            options_list = []
            for option_data in node_data.options:
                # Recursively create child nodes
                child_node = cls._process_story_node(
                    db, story_id, option_data.nextNode, is_root=False
                )
                options_list.append({"text": option_data.text, "node_id": child_node.id})

            node.options = options_list

        db.flush()
        return node
