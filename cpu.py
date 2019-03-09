import pyglet

LOGGING = True
def log(msg):
    if LOGGING:
        print(msg)

class Cpu(pyglet.window.Window):
    def __init__(self):
        self.funcmap = {0x0000: self._0ZZZ,
                        0x00e0: self._0ZZ0,
                        0x00ee: self._0ZZE,
                        0x1000: self._1ZZZ,
                        0x2000: self._2ZZZ,
                        0x3000: self._3ZZZ,
                        0x4000: self._4ZZZ,
                        0x5000: self._5ZZZ,
                        0x6000: self._6ZZZ,
                        0x7000: self._7ZZZ,
                        0x8000: self._8ZZZ,
                        0x8ff0: self._8ZZ0,
                        0x8ff1: self._8ZZ1,
                        0x8ff2: self._8ZZ2,
                        0x8ff3: self._8ZZ3,
                        0x8ff4: self._8ZZ4,
                        0x8ff5: self._8ZZ5,
                        0x8ff6: self._8ZZ6,
                        0x8ff7: self._8ZZ7,
                        0x8ffe: self._8ZZE
                        }
    memory = [0]*4096  # max 4096
    gpio = [0]*16      # max 16
    display_buffer = [0]*64*32
    stack = []
    key_inputs = [0]*16
    opcode = 0
    index = 0

    delay_timer = 0
    sound_timer = 0
    should_draw = False

    pc = 0x200     # First 0x200 (512) bytes are reserved
    vx = 0         # vx and vy are used for passing register numbers
    vy = 0         # in cycle

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
        self.vx = 0         # vx and vy are used for passing register numbers
        self.vy = 0         # in cycle

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
            # print(binary[i])
            self.memory[i+0x200] = binary[i]
            i += 1

    def cycle(self):
        self.opcode = self.memory[self.pc]

        # TODO: process the opcode
        # Fetch the vx and vy specified in the opcode
        self.vx = (self.opcode & 0x0f00) >> 8
        self.vy = (self.opcode & 0x00f0) >> 4
        self.pc += 2    # Don't forget the program counter

        extracted_op = self.opcode & 0xf000
        try:
            self.funcmap[extracted_op]()
        except:
            print("Unknown instruction: %X" % self.opcode)

        # decrement timers
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1
            if self.sound_timer == 0:
                # Play a sound!
                print("sound")

    def draw(self):
        if self.should_draw:
            # draw
            self.clear()
            line_counter = 0
            i = 0
            while i < 2048:
                if self.display_buffer[i] == 1:
                    # draw a square pixel
                    self.pixel.blit((i%64)*10, 310 - ((i/64)*10))
                i += 1
            self.flip()
            self.should_draw = False

    def on_key_press(self, symbol, modifiers):
        log("Key pressed: %r" % symbol)
        if symbol in KEY_MAP.keys():
            self.key_inputs[KEY_MAP[symbol]] = 1
            if self.key_wait:
                self.key_wait = False
        else:
            super(cpu, self).on_key_press(symbol, modifiers)

    def on_key_release(self, symbol, modifiers):
        log("Key released: %r" % symbol)
        if symbol in KEY_MAP.keys():
            self.key_inputs[KEY_MAP[symbol]] = 0

    # Opcode handlers
    def _0ZZZ(self):
        extracted_op = self.opcode & 0xf0ff
        try:
            self.funcmap[extracted_op]()
        except:
            print("Unknown instruction: %X" % self.opcode)

    def _8ZZZ(self):
        extracted_op = self.opcode & 0xf00f
        extracted_op += 0x0ff0
        try:
            self.funcmap[extracted_op]()
        except:
            print("Unknown instruction: %X" % self.opcode)

    # Operations

    def _0ZZ0(self):
        # 00E0 - CLS
        # Clear the display
        log("Clears the screen")
        self.display_buffer = [0]*64*32
        self.should_draw = True

    def _0ZZE(self):
        # 00EE - RET
        # Returns from a subroutine
        log("Returns from subroutine")
        self.pc = self.stack.pop()

    def _1ZZZ(self):
        # 1nnn - JP addr
        # Jump to location nnn.
        log("Jumps to address NNN.")
        self.pc = self.opcode & 0x0fff

    def _2ZZZ(self):
        # 2nnn - CALL addr
        # Call subroutine at nnn.
        log("Jumps to subroutine at address NNN")
        self.stack.append(self.pc)
        self.pc = self.opcode & 0x0fff

    def _3ZZZ(self):
        # 3xkk - SE Vx, byte
        # Skips next instruction if Vx = kk
        if (self.gpio[self.vx]) == (self.opcode & 0x00ff):
            self.pc += 2

    def _4ZZZ(self):
        # 4xkk SNE Vx,  byte
        # The interpreter compares register Vx to kk, and if they are not equal,
        # increments the program counter by 2.
        log("Skips the next instruction if VX doesn't equal NN.")
        if self.gpio[self.vx] != (self.opcode & 0x00ff):
            self.pc += 2

    def _5ZZZ(self):
        # 5xy0 - SE Vx, Vy
        # Skips next instruction if Vx = Vy
        log("Skips the next instruction if VX equals VY")
        if self.gpio[self.vx] == self.gpio[self.vy]:
            self.pc += 2

    def _6ZZZ(self):
        # 6xkk - LD Vx, byte
        # Set Vx = kk
        log("Sets VX to KK")
        self.gpio[self.vx] = (opcode & 0x00ff)

    def _7ZZZ(self):
        # 7xkk - ADD Vx, byte
        # Set Vx = Vx + kk
        log("Sets VX to VX + KK")
        self.gpio[self.vx] += (opcode & 0x00ff)

    def _8ZZ0(self):
        # 8xy0 - LD Vx, Vy
        # Set Vx = Vy
        log("Sets VX to VY")
        self.gpio[self.vx] = self.gpio[self.vy]

    def _8ZZ1(self):
        # 8xy1 - OR Vx, Vy
        # Set Vx = Vx OR Vy
        log("Sets Vx to Vx OR Vy")
        self.gpio[self.vx] |= self.gpio[self.vy]

    def _8ZZ2(self):
        # 8xy2 - AND Vx, Vy
        # Set Vx = Vx AND Vy
        log("Sets Vx to Vx AND Vy")
        self.gpio[self.vx] &= self.gpio[self.vy]

    def _8ZZ3(self):
        # 8xy3 - XOR Vx, Vy
        # Set Vx = Vx XOR Vy
        log("Sets Vx to Vx XOR Vy")
        self.gpio[self.vx] ^= self.gpio[self.vy]

    def _8ZZ4(self):        #TODO: handle 8ZZZ calls
        # 8xy4 - ADD Vx, Vy
        # Set Vx = Vx + Vy, set VF=carry
        log("Adds VY to VX. VF is set to 1 when there's a carry, \
        \and to 0 when there isn't.")
        if self.gpio[self.vx] + self.gpio[self.vy] > 0x44:
            self.gpio[0xf] = 1
        else:
            self.gpio[0xf] = 0
        self.gpio[self.vx] += self.gpio[self.vy]
        self.gpio[self.vx] &= 0xff

    def _8ZZ5(self):
        # 8xy5 - SUB Vx, Vy
        # Set Vx = Vx - Vy set VF = NOT borrow
        log("Sets Vx to Vx - Vy. Sets VF to 1 if there is no borrow")
        if self.gpio[self.vx] > self.gpio[self.vy]:
            self.gpio[0xf] = 1
        else:
            self.gpio[0xf] = 0
        self.gpio[self.vx] -= self.gpio[self.vy]
        self.gpio[self.vx] &= 0xff

    def _8ZZ6(self):
        # 8xy6 - SHR Vx {, Vy}
        # Set Vx = Vx SHR 1
        log("Shifts Vx right once, potential carry stored in VF")
        if (self.gpio[self.vx] & 0x01) == 1:
            self.gpio[0xf] = 1
        else:
            self.gpio[0xf] = 0
        self.gpio[self.vx] /= 2
        self.gpio[self.vx] &= 0xff

    def _8ZZ7(self):
        # 8xy7 - SUBN Vx, Vy
        # Set Vx = Vy - Vx, set Vf = NOT borrow
        log("Subtracts Vx from Vy and stores the result in Vx. Sets Vf to NOT\
        borrow")
        if self.gpio[self.vy] > self.gpio[self.vx]:
            self.gpio[0xf] = 1
        else:
            self.gpio[0xf] = 0
        self.gpio[self.vx] = self.gpio[self.vy] - self.gpio[self.vx]
        self.gpio[self.vx] &= 0xff

    def _8ZZE(self):
        # 8xyE - SHL Vx {, Vy}
        # Shift Vx left
        log("Shifts Vx left once, potential carry stored in VF")
        if (self.gpio[self.vx] & 0x80) == 1:
            self.gpio[0xf] = 1
        else:
            self.gpio[0xf] = 0
        self.gpio[self.vx] *= 2
        self.gpio[self.vx] &= 0xff


    def _FZ29(self):
        log("Set index to point to a character")
        self.index = (5*(self.gpio[self.vx])) & 0xfff

    def _DZZZ(self):
        log("Draw a sprite")
        self.gpio[0xf] = 0
        x = self.gpio[self.vx] & 0xff
        y = self.gpio[self.vy] & 0xff
        height = self.opcode & 0x000f
        row = 0
        while row < height:
            curr_row = self.memory[row + self.index]
            pixel_offset = 0
            while pixel_offset < 8:
                loc = x + pixel_offset + ((y + row) * 64)
                pixel_offset += 1
                if (y + row) >= 32 or (x + pixel_offset - 1) >= 64:
                    #ignore pixels outside the screen
                    continue
                mask = 1 << 8-pixel_offset
                curr_pixel = (curr_row & mask) >> (8-pixel_offset)
                self.display_buffer[loc] ^= curr_pixel
                if self.display_buffer[loc] == 0:
                    self.gpio[0xf] = 1
                else:
                    self.gpio[0xf] = 0
            row += 1
        self.should_draw = true

cpu = Cpu()
cpu.load_rom("Games/TETRIS")
cpu.cycle()
