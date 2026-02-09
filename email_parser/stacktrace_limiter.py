def limit_stacktrace(text: str, max_lines=10) -> str:
    lines = text.splitlines()
    output = []
    stack_started = False

    for line in lines:
        if "Stacktrace" in line:
            stack_started = True

        if stack_started:
            output.append(line)
            if len(output) >= max_lines:
                break
        else:
            output.append(line)

    return "\n".join(output)
