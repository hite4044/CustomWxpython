def parse_flag(flag: int, *allowed_flags: int, default=0):
    for allowed_flag in allowed_flags:
        if flag & allowed_flag:
            return allowed_flag
    return default
