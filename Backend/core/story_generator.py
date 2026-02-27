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

        # --- THE BULLDOZER EXTRACTION ---
        response_text = ""
        if isinstance(raw_response, str):
            response_text = raw_response
        elif isinstance(raw_response, dict):
            response_text = (
                raw_response.get("content")
                or raw_response.get("text")
                or (raw_response.get("choices", [{}])[0].get("message", {}).get("content"))
                or (raw_response.get("choices", [{}])[0].get("text"))
                or str(raw_response)
            )
        elif hasattr(raw_response, "content"):
            response_text = raw_response.content
        else:
            response_text = str(raw_response)

        # Clean Markdown
        if "```" in response_text:
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", response_text, re.DOTALL)
            if match:
                response_text = match.group(1)
        response_text = response_text.strip()

        try:
            story_structure = story_parser.parse(response_text)
        except Exception as e:
            print(f"CRITICAL DEBUG: Raw Response Type: {type(raw_response)}")
            print(f"CRITICAL DEBUG: Raw Response Content: {raw_response}")
            raise ValueError(f"AI returned invalid format: {str(e)}")

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
        # Use getattr to handle both objects and dicts safely
        content = getattr(
            node_data, "content", node_data.get("content") if isinstance(node_data, dict) else ""
        )
        is_ending = getattr(
            node_data,
            "isEnding",
            node_data.get("isEnding") if isinstance(node_data, dict) else True,
        )
        is_winning_ending = getattr(
            node_data,
            "isWinningEnding",
            node_data.get("isWinningEnding") if isinstance(node_data, dict) else False,
        )
        options = getattr(
            node_data, "options", node_data.get("options") if isinstance(node_data, dict) else []
        )

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

        if not is_ending and options:
            options_list = []
            for option_data in options:
                # Handle Pydantic objects or raw dicts
                text = getattr(
                    option_data,
                    "text",
                    option_data.get("text") if isinstance(option_data, dict) else "",
                )
                next_node = getattr(
                    option_data,
                    "nextNode",
                    option_data.get("nextNode") if isinstance(option_data, dict) else None,
                )

                if next_node:
                    child_node = cls._process_story_node(db, story_id, next_node, is_root=False)
                    options_list.append({"text": text, "node_id": child_node.id})

            node.options = options_list

        db.flush()
        return node
