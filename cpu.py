import pyglet
import random
import time

from pyglet.sprite import Sprite

LOGGING = True
def log(msg):
    if LOGGING:
        print(msg)

KEY_MAP = {pyglet.window.key._1: 0x1,
           pyglet.window.key._2: 0x2,
           pyglet.window.key._3: 0x3,
           pyglet.window.key._4: 0xc,
           pyglet.window.key.Q: 0x4,
           pyglet.window.key.W: 0x5,
           pyglet.window.key.E: 0x6,
           pyglet.window.key.R: 0xd,
           pyglet.window.key.A: 0x7,
           pyglet.window.key.S: 0x8,
           pyglet.window.key.D: 0x9,
           pyglet.window.key.F: 0xe,
           pyglet.window.key.Z: 0xa,
           pyglet.window.key.X: 0,
           pyglet.window.key.C: 0xb,
           pyglet.window.key.V: 0xf
          }

class Cpu(pyglet.window.Window):
    def __init__(self):
        super(Cpu, self).__init__()
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
                        0x8ffe: self._8ZZE,
                        0xA000: self._AZZZ,
                        0xB000: self._BZZZ,
                        0xC000: self._CZZZ,
                        0xD000: self._DZZZ,
                        0xE000: self._0ZZZ,
                        0xE09E: self._EZ9E,
                        0xE0A1: self._EZA1,
                        0xF000: self._DZZZ,
                        0xF007: self._FZ07,
                        0xF00A: self._FZ0A,
                        0xF015: self._FZ15,
                        0xF018: self._FZ18,
                        0xF01E: self._FZ1E,
                        0xF029: self._FZ29,
                        0xF033: self._FZ33,
                        0xF055: self._FZ55,
                        0xF065: self._FZ65
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
    key_wait = False

    pc = 0x200     # First 0x200 (512) bytes are reserved
    vx = 0         # vx and vy are used for passing register numbers
    vy = 0         # in cycle

    pixel = pyglet.resource.image('pixel.png')
    buzz = pyglet.resource.media('buzz.wav', streaming=False)

    batch = pyglet.graphics.Batch()
    sprites = []
    for i in range(0,2048):
        sprites.append(pyglet.sprite.Sprite(pixel,batch=batch))

    fonts = [0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
             0x20, 0x60, 0x20, 0x20, 0x70, # 1
             0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
             0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
             0x90, 0x90, 0xF0, 0x10, 0x10, # 4
             0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
             0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
             0xF0, 0x10, 0x20, 0x40, 0x40, # 7
             0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
             0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
             0xF0, 0x90, 0xF0, 0x90, 0x90, # A
             0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
             0xF0, 0x80, 0x80, 0x80, 0xF0, # C
             0xE0, 0x90, 0x90, 0x90, 0xE0, # D
             0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
             0xF0, 0x80, 0xF0, 0x80, 0x80  # F
             ]

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
        self.key_wait = False

        self.pc = 0x200     # First 0x200 (512) bytes are reserved
        self.vx = 0         # vx and vy are used for passing register numbers
        self.vy = 0         # in cycle

        i = 0
        while i < 80:
            # load 80-char font set
            self.memory[i] = self.fonts[i]
            i += 1

    def main(self, prog):
        self.initialize()
        self.load_rom(prog)
        while(True):
            self.dispatch_events()
            self.cycle()
            self.draw()
            time.sleep(.5)

    def load_rom(self, rom_path):
        log("Loading %s..." % rom_path)
        binary = open(rom_path, "rb").read()
        i = 0
        while i < len(binary):
            self.memory[i+0x200] = binary[i]
            i += 1

    def cycle(self):
        self.opcode = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]
        print("Current opcode: %X" % self.opcode)

        # TODO: process the opcode
        # Fetch the vx and vy specified in the opcode
        self.vx = (self.opcode & 0x0f00) >> 8
        self.vy = (self.opcode & 0x00f0) >> 4
        self.pc += 2    # Don't forget the program counter

        extracted_op = self.opcode & 0xf000
        try:
            self.funcmap[extracted_op]()
        except Exception as e:
            print("Unknown instruction: %X" % self.opcode)
            print(e)

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
                    self.sprites[i].x = (i%64)*10
                    self.sprites[i].y = 310 - ((i//64)*10)
                    self.sprites[i].batch = self.batch
                else:
                    self.sprites[i].batch = None
                i += 1
            self.clear()
            self.batch.draw()
            self.flip()
            self.should_draw = False

    def get_key(self):
        for i in range(16):
            if self.key_inputs[i] == 1:
                return i
        return -1

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
            print(1)
            print("Unknown instruction: %X" % self.opcode)

    def _8ZZZ(self):
        extracted_op = self.opcode & 0xf00f
        extracted_op += 0x0ff0
        try:
            self.funcmap[extracted_op]()
        except:
            print(2)
            print("Unknown instruction: %X" % self.opcode)

    # Operations
    def _0ZZ0(self):
        # 00E0 - CLS
        # Clear the display
        log("Clears the screen\n")
        self.display_buffer = [0]*64*32
        self.should_draw = True

    def _0ZZE(self):
        # 00EE - RET
        # Returns from a subroutine
        log("Returns from subroutine. Old PC: %X" % self.pc)
        self.pc = self.stack.pop()
        log("Return complete. PC is now: %X\n" % self.pc)

    def _1ZZZ(self):
        # 1nnn - JP addr
        # Jump to location nnn.
        log("Jumping to address %X from %X" % ((self.opcode % 0x0fff), self.pc))
        self.pc = self.opcode & 0x0fff
        log("Jump complete. PC is now: %X\n" % self.pc)

    def _2ZZZ(self):
        # 2nnn - CALL addr
        # Call subroutine at nnn.
        log("Jumps to subroutine at address %X from %X", ((self.opcode & 0x0fff), self.pc))
        self.stack.append(self.pc)
        self.pc = self.opcode & 0x0fff
        log("Jump complete, PC is now: %X" % self.pc)

    def _3ZZZ(self):
        # 3xkk - SE Vx, byte
        # Skips next instruction if Vx = kk
        log("Skips next instruction if %X equals %X" % (self.gpio[self.vx], (self.opcode & 0x00ff)))
        if (self.gpio[self.vx]) == (self.opcode & 0x00ff):
            self.pc += 2
            log("Instruction skipped \n")
        else:
            log("Instruction not skipped\n")

    def _4ZZZ(self):
        # 4xkk SNE Vx,  byte
        # The interpreter compares register Vx to kk, and if they are not equal,
        # increments the program counter by 2.
        log("Skips the next instruction if %X doesn't equal NN." % (self.gpio[self.vx], (self.opcode & 0x00ff)))
        if self.gpio[self.vx] != (self.opcode & 0x00ff):
            self.pc += 2
            log("Instruction skipped \n")
        else:
            log("Instruction not skipped\n")

    def _5ZZZ(self):
        # 5xy0 - SE Vx, Vy
        # Skips next instruction if Vx = Vy
        log("Skips the next instruction if %X equals %X" % (self.gpio[self.vx], self.gpio[self.vx]))
        if self.gpio[self.vx] == self.gpio[self.vy]:
            self.pc += 2
            log("Instruction skipped \n")
        else:
            log("Instruction not skipped\n")

    def _6ZZZ(self):
        # 6xkk - LD Vx, byte
        # Set Vx = kk
        log("Sets VX(%X) to %X" % (self.gpio[self.vx], (self.opcode % 0x00ff)))
        self.gpio[self.vx] = (self.opcode & 0x00ff)
        log("V%X is now %X\n" % (self.vx, self.gpio[self.vx]))


    def _7ZZZ(self):
        # 7xkk - ADD Vx, byte
        # Set Vx = Vx + kk
        log("Sets V%X(%X) to VX + KK(%X)" % (self.vx, self.gpio[self.vx], (self.opcode % 0x00ff)))
        self.gpio[self.vx] += (self.opcode & 0x00ff)
        log("V%X is now %X\n" % (self.vx, self.gpio[self.vx]))


    def _8ZZ0(self):
        # 8xy0 - LD Vx, Vy
        # Set Vx = Vy
        log("Sets V%X to V%X" % (self.vx, self.vx))
        self.gpio[self.vx] = self.gpio[self.vy]
        log("V%X is now %X\n" % (self.vx, self.gpio[self.vx]))

    def _8ZZ1(self):
        # 8xy1 - OR Vx, Vy
        # Set Vx = Vx OR Vy
        log("Sets V%X to V%X AND V%X" % (self.vx, self.vx, self.vy))
        self.gpio[self.vx] |= self.gpio[self.vy]
        log("V%X is now %X\n" % (self.vx, self.gpio[self.vx]))

    def _8ZZ2(self):
        # 8xy2 - AND Vx, Vy
        # Set Vx = Vx AND Vy
        log("Sets V%X to Vx AND Vy")
        self.gpio[self.vx] &= self.gpio[self.vy]

    def _8ZZ3(self):
        # 8xy3 - XOR Vx, Vy
        # Set Vx = Vx XOR Vy
        log("Sets Vx to Vx XOR Vy")
        self.gpio[self.vx] ^= self.gpio[self.vy]

    def _8ZZ4(self):
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
        self.gpio[self.vx] //= 2
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

    def _9ZZ0(self):
        # 9xy0 - SNE Vx, Vy
        # Skips next instruction if Vx != Vy
        log("Skips next instruction if Vx != Vy")
        if self.gpio[self.vx] != self.gpio[self.vy]:
            self.pc += 2

    def _AZZZ(self):
        # Annn - LD I, addr
        # Set index = nnn
        log("Set index to nnn")
        self.index = (self.opcode & 0x0fff)

    def _BZZZ(self):
        # Bnnn - JP V0, addr
        # Jump to location nnn + V0
        log("Set PC to V0 + nnn")
        self.pc = self.gpio[0] + (self.opcode & 0x0fff)

    def _CZZZ(self):
        # Cxkk - RND Vx, byte
        # Set Vx = random byte AND kk
        log("Set Vx to a random byte AND kk")
        rand = random.randint(0, 255)
        self.gpio[self.vx] = rand & (self.opcode & 0x00ff)

    def _DZZZ(self):
        # Dxyn - DRW Vx, Vy, nibble
        # Display n-byte sprite starting at memory location I at (Vx, Vy),
        # set VF = collision.
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
        self.should_draw = True

    def _EZ9E(self):
        # Ex9E - SKNP Vx
        # Skip next instruction if key with the value of Vx is pressed
        log("Skip next instruction if key with the value of Vx is pressed")
        if self.key_inputs[self.gpio[vx]] == 1:
            self.pc += 2

    def _EZA1(self):
        # ExA1 - SKNP Vx
        # Skip next instruction if key with the value of Vx is not pressed
        log("Skip next instruction if key with the value of Vx is not pressed")
        if self.key_inputs[self.gpio[vx]] == 0:
            self.pc += 2

    def _FZ07(self):
        # Fx07 - LD Vx, DT
        # Set Vx = delay timer value
        log("Put the value of delay timer into Vx")
        self.gpio[self.vx] = delay_timer

    def _FZ0A(self):
        # Fx0A - LD Vx, K
        # Wait for a key press, store the value of the key in Vx
        log("Waits for a key press and stores the result in Vx")
        ret = self.get_key()
        if ret >= 0:
            self.gpio[self.vx] = ret
        else:
            self.pc -= 2    # Repeat the instruction until we get a key press

    def _FZ15(self):
        # Fx15 - LD DT, Vx
        # Set delay timer = Vx
        log("Set delay timer to Vx")
        self.delay_timer = self.gpio[self.vx]

    def _FZ18(self):
        # Fx18 - LD ST, Vx
        # Set sound timer = Vx
        log("Set sound timer to Vx")
        self.sound_timer = self.gpio[self.vx]

    def _FZ1E(self):
        # Fx1E - ADD I, Vx
        # Set I = I + Vx
        log("Add the value in Vx to I")
        self.index += self.gpio[self.vx]

    def _FZ29(self):
        # Fx29 - LF F, Vx
        # Set I = location of sprite for digit Vx
        log("Set index to point to a character")
        self.index = (5*(self.gpio[self.vx])) & 0xfff

    def _FZ33(self):
        # Fx33 - LD B, Vx
        # Store BCD representation of Vx in memory locations I, I+1, and I+2.
        log("Stores BCD of Vx in I, I+1 and I+2")
        self.memory[index] = self.gpio[self.vx] // 100
        self.memory[index + 1] = (self.gpio[self.vx] % 100) // 10
        self.memory[index + 2] = self.gpio[self.vx] % 10

    def _FZ55(self):
        # Fx55 - LD [I], Vx
        # Store registers V0 through Vx in memory starting at location I
        log("Store register V0 through Vx starting at location I")
        for i in range(self.vx):
            self.memory[index + i] = self.gpio[i]

    def _FZ65(self):
        # Fx65 - LD Vx, [I]
        # Read registers V0 through Vx from memory starting at location I
        log("Read values into V0 through Vx from memory starting at I")
        for i in range(self.vx):
            self.gpio[i] = self.memory[index + i]

cpu = Cpu()
cpu.main("Games/PONG2")
# cpu.initialize()
# cpu.load_rom("Games/PONG")
# while(True):
#     cpu.cycle()
