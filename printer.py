from datetime import datetime

now = lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")

color_codes = {
    "black": "30",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
    "white": "37",
    "gray": "90",
    "light_red": "91",
    "light_green": "92",
    "light_yellow": "93",
    "light_blue": "94",
    "light_magenta": "95",
    "light_cyan": "96",
    "light_white": "97",
}


def printc(content, color: str):
    """输出（可指定颜色）"""
    color_code = color_codes.get(color)
    if color_code:
        print(f"\033[{color_code}m{content}\033[0m")
    else:
        print(content)


class Printer:
    def output(self, content, color: str):
        printc(content, color)

    def red(self, content):
        self.output(content, 'red')

    def green(self, content):
        self.output(content, 'green')

    def yellow(self, content):
        self.output(content, 'yellow')

    def blue(self, content):
        self.output(content, 'blue')


printer = Printer()

if __name__ == '__main__':
    printer.red("Hello")
    printer.yellow("World")
    printer.blue("Hello")
    printer.green("World")
