
class Paginator:
    def __init__(self, array: list | tuple, page: int=1):
        self.array = array
        self.page = page
        self.len = len(self.array)

    def __get_slice(self):
        start = self.page - 1
        stop = start + 1
        return self.array[start:stop]

    def get_page(self):
        # print(self.page)
        page_items = self.__get_slice()
        return page_items

    def has_next(self):
        if self.page < self.len:
            return self.page + 1
        return False

    def has_previous(self):
        if self.page > 1:
            return self.page - 1
        return False

