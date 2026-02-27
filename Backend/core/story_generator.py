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
                temperature=0.7,
            )

        return ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)

    @classmethod
    def generate_story(cls, db: Session, session_id: str, theme: str = "fantasy") -> Story:
        llm = cls._get_llm()
        story_parser = PydanticOutputParser(pydantic_object=StoryLLMResponse)

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", STORY_PROMPT),
                (
                    "human",
                    "Generate a complete adventure story based on the theme: {theme}. \n{format_instructions}",
                ),
            ]
        )

        formatted_prompt = prompt.format_prompt(
            theme=theme, format_instructions=story_parser.get_format_instructions()
        )

        raw_response = llm.invoke(formatted_prompt.to_messages())

        # --- FIX FOR 'dict' object has no attribute 'content' ---
        if isinstance(raw_response, dict):
            # If it's a dict, try to get 'content', otherwise stringify the whole thing
            response_text = raw_response.get("content", str(raw_response))
        elif hasattr(raw_response, "content"):
            # If it's a LangChain Message object
            response_text = raw_response.content
        else:
            # Fallback for strings or other types
            response_text = str(raw_response)
        # -------------------------------------------------------

        # Clean Markdown formatting
        if "```json" in response_text:
            match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
            if match:
                response_text = match.group(1)
        elif "```" in response_text:
            match = re.search(r"```\s*(.*?)\s*```", response_text, re.DOTALL)
            if match:
                response_text = match.group(1)

        response_text = response_text.strip()

        try:
            story_structure = story_parser.parse(response_text)
        except Exception as e:
            print(f"DEBUG: Parsing failed. Content: {response_text}")
            raise ValueError(f"AI returned invalid JSON: {str(e)}")

        story_db = Story(title=story_structure.title, session_id=session_id)
        db.add(story_db)
        db.flush()

        cls._process_story_node(db, story_db.id, story_structure.rootNode, is_root=True)

        db.commit()
        return story_db

    @classmethod
    def _process_story_node(
        cls, db: Session, story_id: int, node_data: StoryNodeLLM, is_root: bool = False
    ) -> StoryNode:
        # Node_data is now guaranteed to be a StoryNodeLLM object by the parser
        node = StoryNode(
            story_id=story_id,
            content=node_data.content,
            is_root=is_root,
            is_ending=node_data.isEnding,
            is_winning_ending=node_data.isWinningEnding,
            options=[],
        )
        db.add(node)
        db.flush()

        if not node_data.isEnding and node_data.options:
            options_list = []
            for option_data in node_data.options:
                child_node = cls._process_story_node(
                    db, story_id, option_data.nextNode, is_root=False
                )
                options_list.append({"text": option_data.text, "node_id": child_node.id})

            node.options = options_list

        db.flush()
        return node
