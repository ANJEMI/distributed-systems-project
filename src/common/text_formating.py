from colorama import Fore, Style, init

# Inicializar colorama (importante en Windows)
init(autoreset=True)

def print_formated(text, color="white"):
    colors = {
        "red": Fore.RED,
        "green": Fore.GREEN,
        "yellow": Fore.YELLOW,
        "blue": Fore.BLUE,
        "magenta": Fore.MAGENTA,
        "cyan": Fore.CYAN,
        "white": Fore.WHITE
    }

    selected_color = colors.get(color.lower(), Fore.WHITE)
    
    print(f"\n\n{selected_color}{text}{Style.RESET_ALL}\n\n")

