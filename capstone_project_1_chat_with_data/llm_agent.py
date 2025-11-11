from db_manager import SteamDBManager
from issue_manager import GitHubIssueError, create_github_issue

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

LOG_BUFFER: list[str] = []

def log(message: str) -> None:
    LOG_BUFFER.append(message)
    print(message)


class LLMAgent:
    def __init__(self, db_path: str, model: str = "gpt-4o-mini", temperature: float = 0.2) -> None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set in environment variables.")

        log("Initializing OpenAI client...")
        self.client = OpenAI(api_key=api_key)
        self.db_manager = SteamDBManager(db_path)
        log(f"Database manager initialised with {db_path}")
        self.model = model
        self.temperature = temperature

        self.system_prompt = {
            "role": "system",
            "content": (
                "You are a helpful assistant with access to a SQLite database containing a single table named "
                "'steam_games'. Available columns are: appid, name, release_date, english, developer, publisher, "
                "platforms, required_age, categories, genres, steamspy_tags, achievements, positive_ratings, "
                "negative_ratings, average_playtime, median_playtime, owners, price. "
                "Always reference this table exactly by name and only use the listed columns."
            ),
        }

    def _get_functions(self) -> list[dict[str, any]]:
        return [
            {
                "type": "function",
                "name": "execute_sql_query",
                "description": "Executes a SQL SELECT query and returns the result.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "SQL SELECT statement."},
                        "parameters": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Parameters for ? placeholders in the query.",
                            "default": [],
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "type": "function",
                "name": "search_game_by_name",
                "description": "Returns games whose names contain the provided text.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Substring of the game title."},
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results.",
                            "default": 5,
                        },
                    },
                    "required": ["name"],
                },
            },
            {
                "type": "function",
                "name": "get_genre_counts",
                "description": "Returns counts of games per genre for chart visualizations.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "How many genres to return.",
                            "default": 10,
                        },
                    },
                },
            },
            {
                "type": "function",
                "name": "create_github_issue",
                "description": "Creates a GitHub issue with the provided title, body and optional labels.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Issue title."},
                        "body": {"type": "string", "description": "Issue body content."},
                        "labels": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of labels to assign.",
                        },
                    },
                    "required": ["title", "body"],
                },
            },
        ]

    def _call_function(self, name: str, arguments: dict[str, any]) -> dict[str, any]:
        if name == "execute_sql_query":
            query = arguments["query"]
            params = tuple(arguments.get("parameters", []))
            rows = self.db_manager.execute_query(query, params)
            return {"rows": rows, "count": len(rows)}

        if name == "search_game_by_name":
            name_value = arguments["name"]
            limit = int(arguments.get("limit", 5))
            rows = self.db_manager.search_games(name_value, limit=limit)
            return {"rows": rows, "count": len(rows)}

        if name == "get_genre_counts":
            limit = int(arguments.get("limit", 10))
            query = """
                SELECT genres, COUNT(*) AS total
                FROM steam_games
                WHERE genres IS NOT NULL AND genres != ''
                GROUP BY genres
                ORDER BY total DESC
                LIMIT ?
            """
            rows = self.db_manager.execute_query(query, (limit,))
            genre_counter: dict[str, int] = {}
            for row in rows:
                for genre in row["genres"].split(";"):
                    genre = genre.strip()
                    if not genre:
                        continue
                    genre_counter[genre] = genre_counter.get(genre, 0) + row["total"]

            top_items = sorted(genre_counter.items(), key=lambda item: item[1], reverse=True)[:limit]
            return {"genres": [{"genre": genre, "count": count} for genre, count in top_items]}

        if name == "create_github_issue":
            title = arguments["title"]
            body = arguments["body"]
            labels = arguments.get("labels")
            try:
                issue = create_github_issue(title=title, body=body, labels=labels)
            except GitHubIssueError as error:
                log(f"Failed to create GitHub issue: {error}")
                return {"error": str(error)}
            log(f"Issue created: {issue.get('html_url')}")
            return {
                "number": issue.get("number"),
                "title": issue.get("title"),
                "url": issue.get("html_url"),
            }

        raise ValueError(f"Unknown function call: {name}")

    def generate(self, messages: list[dict[str, str]]) -> dict[str, any]:
        conversation = [self.system_prompt] + messages
        response = self.client.responses.create(
            model=self.model,
            temperature=self.temperature,
            input=conversation,
            tools=self._get_functions(),
        )

        if response.output:
            messages += response.output
            for item in response.output:
                if item.type == "message" and item.role == "assistant":
                    log(f"Message was generated: {item.content}")
                    content = item.content
                    text = ""
                    for part in content:
                        if part.type == "output_text":
                            text += part.text
                    return {
                        "content": text,
                        "usage": {
                            "input_tokens": response.usage.input_tokens if response.usage else None,
                            "output_tokens": response.usage.output_tokens if response.usage else None,
                            "total_tokens": response.usage.total_tokens if response.usage else None,
                        },
                    }

                if item.type == "function_call":
                    name = item.name
                    arguments = item.arguments or {}
                    if isinstance(arguments, str):
                        arguments = json.loads(arguments)
                    log(f"Tool call requested: {name} with args {arguments}")
                    call_result = self._call_function(name, arguments)
                    log(f"Tool result: {call_result}")
                    messages.append(
                        {
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": json.dumps(call_result),
                        }
                    )
                    return self.generate(messages)

        return {"content": None, "usage": {}}

