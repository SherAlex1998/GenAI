from __future__ import annotations

from llm_agent import LLMAgent


def main() -> None:
    db_path = "steam.sqlite"
    agent = LLMAgent(db_path=db_path)
    conversation: list[dict[str, str]] = []

    print("Введите запрос агенту (quit/exit для выхода).")
    while True:
        try:
            user_input = input("Вы: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nЗавершение работы.")
            break

        if user_input.lower() in {"quit", "exit"}:
            print("Выход.")
            break

        if not user_input:
            continue

        conversation.append({"role": "user", "content": user_input})
        try:
            result = agent.generate(conversation.copy())
        except Exception as exc:  # noqa: BLE001
            print(f"Агент: Ошибка — {exc}")
            continue

        answer = result.get("content") or "Ответ не получен."
        print(f"Агент: {answer}")
        conversation.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()

