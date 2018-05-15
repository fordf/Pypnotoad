from pygame import Rect

class RelativeRect(Rect):
    def __init__(self, client_rect):
        self.client_rect = client_rect

    @Rect.x.getter
    def x(self):
        return self.client_rect.x - super().x