from enum import Enum, IntEnum
from typing import Self, Callable, Any, TypeVar
from xml.etree import ElementTree as ET
import re

############
# Settings #
############



#####################
# Utility functions #
#####################

def upper_hex(number : int, padding : int):
    """Creates an uppercase hexadecimal string such as "#123456\""""
    return str(hex(number))[2:].ljust(padding, '0').upper()

#################
# Value objects #
#################

class ObjectHashHolder:
    value : int

    def __init__(self, value : int = 0) -> None:
        self.value = value
    def add(self, value : int, size : int) -> None:
        self.value <<= size
        self.value += 0 if value is None else value

class Colour:
    """Contains colour values for pens"""
    value : int
    
    def __init__(self, rgb : int) -> None:
        """
        Initialises a colour value from an integer RGB code.

        Parameters:
            rgb (int): The hexadecimal RGB code as an integer between
                       0x000000 and 0xffffff inclusive.
        """
        if rgb < 0 or rgb > 0xffffff:
            raise ValueError("Colour value out of range: %s" % rgb)
        self.value = rgb

    def __repr__(self):
        return "#" + upper_hex(self.value, 6)
    
    @classmethod
    def from_rgb(cls, r : int, g : int, b : int) -> Self:
        """
        Creates a colour value from separate red, green and blue values.

        Parameters:
            r (int): The red value as an integer between 0x00
                and 0xff inclusive.
            
            g (int): The green value as an integer between 0x00
                and 0xff inclusive.
        
            b (int): The blue value as an integer between 0x00
                and 0xff inclusive.
        
        Returns
            Self: A colour with the specified red, green
                and blue values.
        """
        if r < 0 or r > 0xff:
            raise ValueError("Red value out of range: %s" % r)
        if g < 0 or g > 0xff:
            raise ValueError("Green value out of range: %s" % g)
        if b < 0 or b > 0xff:
            raise ValueError("Blue value out of range: %s" % b)
        return cls(r*0x10000 + g*0x100 + b)

class FontSize:
    value : int

    def __init__(self, value : int) -> None:
        self.value = value

    @classmethod
    def frac(cls, value : float) -> Self:
        """Converts fractional relative size to size value for YTT"""
        argval = int(value * 400 - 300)
        if argval < 0:
            raise ValueError(f"Text size cannot be less than 0.75; given {value:1.2}")
        return cls(argval)

    def get_frac(self) -> float:
        """Converts stored YTT size value to fractional relative size"""
        return self.value/400 + 0.75

class ScreenPos:
    """Contains position values for windows,
       and fuctions to set adjusted positions."""
    x : int
    y : int

    def __init__(self, x, y) -> None:
        self.x : int = x
        self.y : int = y

class Edge(IntEnum):
    """Edge typee values"""
    HARD = 1
    BEVEL = 2
    GLOW = 3
    SHADOW = 4

class Font(IntEnum):
    """Font face values"""
    SERIF = 1
    SERIF_MONO = 2
    SANS = 3
    SANS_MONO = 4
    CASUAL = 5
    CURSIVE = 6
    SMALLCAPS = 7

class VOffset(IntEnum):
    """Offset values regulating subscript and superscript"""
    SUBSCRIPT = 0
    SUPERSCRIPT = 2

class Ruby(IntEnum):
    """Ruby text values"""
    CONTENT = 1
    BRAKETS = 2
    ABOVE = 4
    BELOW = 5

class Anchor(IntEnum):
    """Anchor value for subtitle windows"""
    TOP_LEFT = 0
    TOP_CENTRE = 1
    TOP_RIGHT = 2
    CENTRE_LEFT = 3
    CENTRE = 4
    CENTRE_RIGHT = 5
    BOTTOM_LEFT = 6
    BOTTOM_CENTRE = 7
    BOTTOM_RIGHT = 8

class TextDirection(IntEnum):
    """Text direction values for subtitle windows"""
    RTL = 1
    VERTICAL = 2
    ROTATED_90ACW = 3

class Justify(IntEnum):
    """Text alignment values for subtitle windows"""
    LEFT = 0
    RIGHT = 1
    CENTRE = 2

Align = Justify

####################
# Pens and windows #
####################

class Pen:
    """ A YTT pen, containing styling information for text """
    __slots__ = ("bold",
                 "italics",
                 "under",
                 "strike",
                 "colour",
                 "opacity",
                 "bg_colour",
                 "bg_opacity",
                 "edge",
                 "edge_colour",
                 "edge_opacity",
                 "font_face",
                 "font_size",
                 "ruby")

    def __init__(self, **properties):
        """
        Initialises a pen.
        Allowed parameters for properties are:
            base (string-like): the pen this is a variant of
            bold (bool): Whether or not the text is bold
            italics (bool): Whether or not the text is italic
            under (bool): Whether or not the text is underlined
            strike (bool): Whether or not the text is struck through
            colour (Colour): Text colour
            opacity (int): Text opacity
            bg_colour (Colour): Background colour
            bg_opacity (int): Background opacity
            edge (Edge): Text edge type
            edge_colour (Colour): Text edge colour
            edge_opacity (int): Text edge opacity
            font_face (Font): Font used by the text
            font_size (FontSize): Size of text
            ruby (Ruby): Furigana mode
            """
        for name in properties.keys():
            setattr(self, name, properties[name])
    
    def __getattr__(self, name):
        if name in self.__slots__:
            return None
        else:
            raise AttributeError(f"Invalid pen attribute: {name}")
    
    def full(self):
        d = dir(self)
        for name in self.__slots__:
            if name not in d:
                return False
        return True

    def eq_attr(self, name, value):
        if self not in __slots__:
            raise ValueError(f"Invalid pen attribute: {name}")
        return (value == getattr(self, value))

    def __eq__(self, other):
        for name in self.__slots__:
            if not other.eq_attr(name, getattr(self, value)):
                return False
        return True

class Window:
    __slots__ = ("base_pen",
                 "pos",
                 "anchor",
                 "justify",
                 "text_dir")

    def __init__(self, base_pen : Pen, **properties):
        """
        Initialises a window. base_pen parameter sets the default pen for the window.
        
        Allowed parameters for properties are:
            pos (ScreenPos): Position of the window on the screen
            anchor (Anchor): Window anchoring point
            justify (Justify): Window text alignment
            text_dir (TextDirection): Window text direction
        """
        for name in properties.keys():
            setattr(self, name, properties[name])
    
    def __getattr__(self, name):
        if name in self.__slots__:
            return None
        else:
            raise AttributeError(f"Invalid window attribute: {name}")
    
    def full(self):
        d = dir(self)
        for name in self.__slots__:
            if name not in d:
                return False
        return True

    def eq_attr(self, name, value):
        if self not in __slots__:
            raise ValueError(f"Invalid window attribute: {name}")
        return (value == getattr(self, value))

    def __eq__(self, other):
        for name in self.__slots__:
            if not other.eq_attr(name, getattr(self, value)):
                return False
        return True

#############################
# Command syntax definition #
#############################

class SyntaxConstDef:
    """ Definition of syntax constants (individual symbols) """
    value : str
    
    def __init__(self, symbol : str):
        self.value = re.escape(symbol)

    def re(self) -> str:
        return re.escape(self.value)

CMD_OP = SyntaxConstDef("\\") # Command starter
CMD_ARG_OP = SyntaxConstDef("{") # Command argument opener
CMD_ARG_SP = SyntaxConstDef(",") # Command argument separator
CMD_ARG_CL = SyntaxConstDef("}") # Command argument closer
CMD_CL = SyntaxConstDef(";") # Command closer

# Regular expression that defines a command.
# Captures the command name and the list of arguments.
CMD_RE = re.compile(CMD_OP.re() + r"(?P<cmd>\w+)" \
                   + r"(?P<args>" + CMD_ARG_OP.re() + r".*?" + CMD_ARG_CL.re() + r")?" \
                   + CMD_CL.re() + r"?")

# Regular expression that defines a list of arguments.
# Captures each command expression.
CMD_ARGS_RE = re.compile(CMD_ARG_OP.re() + r"(.*?)" \
                       + r"(?:" + CMD_ARG_SP.re() + r"(.*?))*" \
                       + CMD_ARG_CL.re())

##############################
# Command definition classes #
##############################

class CmdArgDef:
    """ Generic base class for command argument definitions """
    name : str
    evaluate : Callable[[str], Any] = lambda x : None

    def __init__(self, name : str, evaluate : Callable[[str], Any]) -> None:
        self.name = name
        self.evaluate = evaluate
    
class StrArgDef(CmdArgDef):
    """ Generic string argument definition """
    def __init__(self, name : str) -> Self:
        super().__init__(name, str)

class IntArgDef(CmdArgDef):
    """ Generic integer argument definition """    
    def __init__(self, name : str) -> Self:
        super().__init__(name, int)

class IntEnumArgDef(CmdArgDef):
    """ Generic integer enum argument definition """
    enum : type[IntEnum]
    
    def eval_int_enum(value : str):
        try:
            return enum(int(value))
        except ValueError:
            return enum[value]
    
    def __init__(self, name : str, enum : type[Enum]) -> Self:
        self.enum = enum
        super().__init__(name, self.eval_int_enum)

class ColourArgDef(CmdArgDef):
    """ Generic colour argument definition """
    @staticmethod
    def eval_colour(value : str):
        return int(value.replace("#", ""), base=16)
    
    def __init__(self, name : str) -> Self:
        super().__init__(name, self.eval_colour)
ColorArgDef = ColourArgDef

class SizeArgDef(CmdArgDef):
    """ Generic font size argument definition """
    @staticmethod
    def eval_size(value: str):
        return FontSize.frac(float(value))
        
    def __init__(self, name : str) -> Self:
        super().__init__(name, self.eval_size)

class CmdDef:
    """ A command definition for syntax commands """
    name : str
    args : list[str]
    apply : Callable[[Self, ET.Element], ET.Element] = lambda x : None
    def __init__(self, name : str, *args : CmdArgDef) -> None:
        self.name = name
        self.args = args
    
    def __repr__(self) -> str:
        txt = CMD_OP.value + self.name
        if self.args is not None and len(self.args) > 0:
            arg_names = [("<%s>" % arg.name) for arg in self.args]
            txt = txt + CMD_ARG_OP.value + CMD_ARG_OP.value.join(arg_names) \
                  + CMD_ARG_CL.value
        return txt
    
    def get_arg(self, name : str) -> Any:
        for arg in self.args:
            if arg.name == name:
                return arg.evaluate()

class ReadCmd:
    cmd_def: CmdDef
    arg_list : list
    def __init__(self, cmd_def : CmdDef, args : list[str|None]):
        if len(args) > len(cmd_def.args):
            raise ValueError(f"List of arguments for {cmd_def.name} is too long")
        self.cmd_def = cmd_def
        self.arg_list = list(len(args))
        for i, arg in enumerate(args):
            if arg is not None:
                self.arg_list[i] = cmd_def.args[i].evaluate(arg)
        
###################
# Command actions #
###################

class 

#######################
# Command definitions #
#######################

CMD_BOLD = CmdDef("b")
CMD_ITALICS = CmdDef("i")
CMD_UL = CmdDef("u")
CMD_STRIKE = CmdDef("s")

CMD_ARG_COLOUR = ColourArgDef("colour")
CMD_ARG_OPACITY = IntArgDef("opacity")
CMD_ARG_EDGE = IntEnumArgDef("edge", Edge)

CMD_FG = CmdDef("fg", CMD_ARG_COLOUR, CMD_ARG_OPACITY)
CMD_BG = CmdDef("bg", CMD_ARG_COLOUR, CMD_ARG_OPACITY)
CMD_EDGE = CmdDef("edge", CMD_ARG_EDGE, CMD_ARG_COLOUR, CMD_ARG_OPACITY)

CMD_ARG_FONT = IntEnumArgDef("font", Font)
CMD_FONT = CmdDef("ff", CMD_ARG_FONT)

CMD_ARG_SIZE = SizeArgDef("size")
CMD_SIZE = CmdDef("sz", CMD_ARG_SIZE)

CMD_ARG_RUBY = IntEnumArgDef("ruby", Ruby)
CMD_RUBY = CmdDef("ruby", CMD_ARG_RUBY)

CMD_ARG_PEN_ID = StrArgDef("pen-id")
CMD_NEWPEN = CmdDef("newpen", CMD_ARG_PEN_ID)
CMD_PEN = CmdDef("p", CMD_ARG_PEN_ID)
CMD_PEN_RESET = CmdDef("r")

##############
# THE PARSER #
##############

class PenBase:
    name : str
    base : Pen
    variants : list(Pen)

class PenTracker:
    pens : list(PenBase) = []
    indices : dict(str, int) = dict()
    
    def append(self, item : PenVariant):
        self.pens.append(item)
        self.indices[item.name] = len(self.pens) - 1
    
    def get_id(self, name : str, var : int | None = None):
        id = 1
        pen_idx = self.indices[name]
        for i in range(pen_idx):
            id += len(self.pens[i]) + 1
        if var is None:
            return str(id)
        else:
            return str(id + var + 1)

class PenRef:
    name : str
    tracker : PenTracker
    variant : int | None
    
    def __init__(self, tracker : PenTracker, name : str, var : int | None = None):
        self.tracker = tracker
        self.name = name
        self.var = variant
        
    def __repr__(self):
        return self.tracker.get_id(self.name, self.var)
        
class ParserPhase(Enum):
    HEAD
    BODY

class DocTracker:
    doc : ET.ElementTree
    pens : PenTracker
    windows :
    curr_pen : Pen
    curr_win : Window
    
    
class Parser:
    _curr : str
    _doc : DocTracker
    _cmds = dict(str, CmdDef)

    def __init__(self):
        pass

    def parse_lines(self, lines : list[str]) -> ET.ElementTree:
        _doc = ET.ElementTree()
        for line in lines:
            self._parse_line(line)
        doc = self._clear_parser()
        return _doc

    def _parse_line(self, line: str):
        pass
        
    
    





