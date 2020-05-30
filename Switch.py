from Node import Node


class Switch(Node):
    def __init__(self, x, y, scale, batch):
        super().__init__(x, y, scale * 1.5, batch)

    def flip(self):
        """ toggle switch on / off """
        self.powered = not self.powered
        self._update_image()
        for child in self.children: child.update()

    def update_power(self, source = None):
        """ removed update_power functionality as this is only a source """
        pass
