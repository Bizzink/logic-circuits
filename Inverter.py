from Node import Node


class Inverter(Node):
    def __init__(self, x, y, scale, batch):
        super().__init__(x, y, scale, batch)
        self.powered = True

    def update_power(self):
        """ Invert typical powered function """
        prev_power = self.powered

        self.powered = True
        if any([source.powered for source in self.sources]): self.powered = False

        # preform updates only if power state has changed
        if self.powered != prev_power:
            self._update_image()
            for child in self.children: child.update()
