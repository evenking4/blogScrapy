from dateutil import parser

def format_time_str(raw_time_str, target_format="%Y-%m-%d"):
    try:
        # dateutil.parser 能够自动识别大多数常见的时间格式
        parsed_date = parser.parse(raw_time_str)
        # 格式化为你需要的统一字符串，例如 "2019-12-31"
        return parsed_date.strftime(target_format)
    except Exception as e:
        print(f"解析失败: {raw_time_str}, 错误原因: {e}")
        return None