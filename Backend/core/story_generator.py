@classmethod
    def generate_story(cls, db: Session, session_id: str, theme: str = "fantasy") -> Story:
        llm = cls._get_llm()
        story_parser = PydanticOutputParser(pydantic_object=StoryLLMResponse)

        prompt = ChatPromptTemplate.from_messages([
            ("system", STORY_PROMPT),
            ("human", "Generate a complete adventure story based on the theme: {theme}. \n{format_instructions}")
        ])

        formatted_prompt = prompt.format_prompt(
            theme=theme, 
            format_instructions=story_parser.get_format_instructions()
        )

        raw_response = llm.invoke(formatted_prompt.to_messages())

        # --- THE BULLDOZER EXTRACTION ---
        response_text = ""
        
        if isinstance(raw_response, str):
            response_text = raw_response
        elif isinstance(raw_response, dict):
            # Try every common key used by different LLM wrappers
            response_text = (
                raw_response.get("content") or 
                raw_response.get("text") or 
                (raw_response.get("choices", [{}])[0].get("message", {}).get("content")) or
                (raw_response.get("choices", [{}])[0].get("text")) or
                str(raw_response) # Final fallback
            )
        elif hasattr(raw_response, "content"):
            response_text = raw_response.content
        else:
            response_text = str(raw_response)
        # --------------------------------

        # Clean Markdown formatting (AI often wraps JSON in backticks)
        if "```" in response_text:
            # Matches content inside ```json ... ``` or just ``` ... ```
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", response_text, re.DOTALL)
            if match:
                response_text = match.group(1)
            
        response_text = response_text.strip()

        try:
            story_structure = story_parser.parse(response_text)
        except Exception as e:
            # This will help you see the EXACT dictionary structure in your logs
            print(f"CRITICAL DEBUG: Raw Response Type: {type(raw_response)}")
            print(f"CRITICAL DEBUG: Raw Response Content: {raw_response}")
            raise ValueError(f"AI returned invalid format: {str(e)}")

        story_db = Story(title=story_structure.title, session_id=session_id)
        db.add(story_db)
        db.flush()

        cls._process_story_node(db, story_db.id, story_structure.rootNode, is_root=True)

        db.commit()
        return story_db