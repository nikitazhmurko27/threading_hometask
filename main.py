from file_manager_utility import FileManagerUtility
import argparse


def get_file_mask(src: str) -> str:
    mask_start = src.find('.')
    if mask_start == -1:
        return ''
    return src[mask_start:]


def get_folder_path(src: str) -> str:
    dot_pos = src.find('.')
    if dot_pos == -1:
        return src
    slash_pos = src.rfind("/""")
    if slash_pos == -1:
        return ''
    return src[:slash_pos]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--operation", help="Operation (copy/move)")
    parser.add_argument("--src", type=str, nargs="*", help="Pathname 'from' folder")
    parser.add_argument("--to", type=str, help="Pathname 'to' folder")
    parser.add_argument("--threads", type=int, help="Amount of threads", default=1)
    option = parser.parse_args()

    file_mask = get_file_mask(option.src[0])
    from_path = get_folder_path(option.src[0])

    fmu = FileManagerUtility(
        option.operation,
        from_path,
        option.to,
        file_mask,
        option.threads
    )
    fmu.start()


if __name__ == '__main__':
    main()
