import pyglet

class Cpu(pyglet.window.Window):
    def initialize(self):
        self.clear()
        self.memory = [0]*4096  # max 4096
        self.gpio = [0]*16      # max 16
        self.display_buffer = [0]*64*32
        self.stack = []
        self.key_inputs = [0]*16
        self.opcode = 0
        self.index = 0

        self.delay_timer = 0
        self.sound_timer = 0
        self.should_draw = False

        self.pc = 0x200     # First 0x200 (512) bytes are reserved

        i = 0
        while i < 80:
            # load 80-char font set
            self.memory[i] = self.fonts[i]
            i += 1

        def load_rom(self, rom_path):
            log("Loading %s..." % rom_path)
            binary = open(rom_path, "rb").read()
            i = 0
            while i < len(binary):
                self.memory[i+0x200] = ord(binary[i])
                i += 1
