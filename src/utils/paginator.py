from typing import Sequence


class Paginator:
    def __init__(self, array: Sequence | tuple, page: int = 1):
        self.array = array
        self.page = page
        self.len = len(self.array)

    def __get_slice(self) -> Sequence | tuple:
        start = self.page - 1
        stop = start + 1
        return self.array[start:stop]

    def get_page(self) -> Sequence | tuple:
        return self.__get_slice()

    def has_next(self) -> bool | int:
        if self.page < self.len:
            return self.page + 1
        return False

    def has_previous(self) -> bool | int:
        if self.page > 1:
            return self.page - 1
        return False
