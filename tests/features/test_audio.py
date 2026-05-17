import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from core.lexer import Lexer
from core.parser import Parser
from core.interpreter import Interpreter
from core.runtime import Runtime
from core.ast import PlayMusicStmt, PlaySoundStmt, StopMusicStmt, StopSoundStmt, SetVolumeStmt


class TestAudioLexer:
    """测试音频词法"""

    def test_music_keyword(self):
        src = 'music "test.mp3"'
        tokens = Lexer(src).tokenize()
        assert tokens[0].type.name == "MUSIC"
        assert tokens[1].type.name == "STRING"
        assert tokens[1].value == "test.mp3"

    def test_sound_keyword(self):
        src = 'sound "test.wav"'
        tokens = Lexer(src).tokenize()
        assert tokens[0].type.name == "SOUND"
        assert tokens[1].type.name == "STRING"
        assert tokens[1].value == "test.wav"

    def test_stop_keyword(self):
        src = 'stop music'
        tokens = Lexer(src).tokenize()
        assert tokens[0].type.name == "STOP"
        assert tokens[1].type.name == "MUSIC"

    def test_volume_keyword(self):
        src = 'volume music = 0.5'
        tokens = Lexer(src).tokenize()
        assert tokens[0].type.name == "VOLUME"
        assert tokens[1].type.name == "MUSIC"
        assert tokens[2].type.name == "ASSIGN"
        assert tokens[3].type.name == "NUMBER"


class TestAudioParser:
    """测试音频语法解析"""

    def parse(self, src: str):
        tokens = Lexer(src).tokenize()
        return Parser(tokens).parse()

    def test_music_basic(self):
        program = self.parse('music "bgm.mp3"')
        stmt = program.statements[0]
        assert isinstance(stmt, PlayMusicStmt)
        assert stmt.path == "bgm.mp3"
        assert stmt.loop == True
        assert stmt.volume == 1.0
        assert stmt.fade_in == 0.0

    def test_music_with_fade(self):
        program = self.parse('music "bgm.mp3" with fade 2.0')
        stmt = program.statements[0]
        assert isinstance(stmt, PlayMusicStmt)
        assert stmt.fade_in == 2.0

    def test_music_with_volume(self):
        program = self.parse('music "bgm.mp3" volume 0.5')
        stmt = program.statements[0]
        assert isinstance(stmt, PlayMusicStmt)
        assert stmt.volume == 0.5

    def test_music_no_loop(self):
        program = self.parse('music "bgm.mp3" loop false')
        stmt = program.statements[0]
        assert isinstance(stmt, PlayMusicStmt)
        assert stmt.loop == False

    def test_music_loop_true(self):
        program = self.parse('music "bgm.mp3" loop true')
        stmt = program.statements[0]
        assert isinstance(stmt, PlayMusicStmt)
        assert stmt.loop == True

    def test_sound_basic(self):
        program = self.parse('sound "sfx.wav"')
        stmt = program.statements[0]
        assert isinstance(stmt, PlaySoundStmt)
        assert stmt.path == "sfx.wav"
        assert stmt.volume == 1.0

    def test_sound_with_volume(self):
        program = self.parse('sound "sfx.wav" volume 0.8')
        stmt = program.statements[0]
        assert isinstance(stmt, PlaySoundStmt)
        assert stmt.volume == 0.8

    def test_stop_music(self):
        program = self.parse('stop music')
        stmt = program.statements[0]
        assert isinstance(stmt, StopMusicStmt)
        assert stmt.fade_out == 0.0

    def test_stop_music_with_fade(self):
        program = self.parse('stop music with fade 3.0')
        stmt = program.statements[0]
        assert isinstance(stmt, StopMusicStmt)
        assert stmt.fade_out == 3.0

    def test_stop_sound(self):
        program = self.parse('stop sound')
        stmt = program.statements[0]
        assert isinstance(stmt, StopSoundStmt)

    def test_volume_music(self):
        program = self.parse('volume music = 0.7')
        stmt = program.statements[0]
        assert isinstance(stmt, SetVolumeStmt)
        assert stmt.music_volume == 0.7

    def test_volume_sound(self):
        program = self.parse('volume sound = 0.5')
        stmt = program.statements[0]
        assert isinstance(stmt, SetVolumeStmt)
        assert stmt.sound_volume == 0.5

    def test_music_in_label(self):
        src = 'label start:\n    music "bgm.mp3"\nend\n'
        program = self.parse(src)
        assert isinstance(program.statements[0].body[0], PlayMusicStmt)


class TestAudioInterpreter:
    """测试音频解释器"""

    def test_play_music_sets_pending_audio(self):
        src = 'music "bgm.mp3"\n'
        interp = Interpreter(runtime=Runtime())
        interp.run(Parser(Lexer(src).tokenize()).parse())
        assert interp.runtime.pending_audio is not None
        assert interp.runtime.pending_audio["type"] == "play_music"

    def test_play_sound_sets_pending_audio(self):
        src = 'sound "sfx.wav"\n'
        interp = Interpreter(runtime=Runtime())
        interp.run(Parser(Lexer(src).tokenize()).parse())
        assert interp.runtime.pending_audio is not None
        assert interp.runtime.pending_audio["type"] == "play_sound"

    def test_stop_music_sets_pending_audio(self):
        src = 'stop music\n'
        interp = Interpreter(runtime=Runtime())
        interp.run(Parser(Lexer(src).tokenize()).parse())
        assert interp.runtime.pending_audio is not None
        assert interp.runtime.pending_audio["type"] == "stop_music"

    def test_stop_sound_sets_pending_audio(self):
        src = 'stop sound\n'
        interp = Interpreter(runtime=Runtime())
        interp.run(Parser(Lexer(src).tokenize()).parse())
        assert interp.runtime.pending_audio is not None
        assert interp.runtime.pending_audio["type"] == "stop_sound"

    def test_volume_music(self):
        src = 'volume music = 0.7\n'
        interp = Interpreter(runtime=Runtime())
        interp.run(Parser(Lexer(src).tokenize()).parse())
        assert interp.runtime.music_volume == 0.7

    def test_volume_sound(self):
        src = 'volume sound = 0.5\n'
        interp = Interpreter(runtime=Runtime())
        interp.run(Parser(Lexer(src).tokenize()).parse())
        assert interp.runtime.sound_volume == 0.5

    def test_music_with_options(self):
        src = 'music "bgm.mp3" loop false volume 0.6\n'
        interp = Interpreter(runtime=Runtime())
        interp.run(Parser(Lexer(src).tokenize()).parse())
        audio = interp.runtime.pending_audio
        assert audio["loop"] == False
        assert audio["volume"] == 0.6

    def test_music_with_fade(self):
        src = 'music "bgm.mp3" with fade 2.0\n'
        interp = Interpreter(runtime=Runtime())
        interp.run(Parser(Lexer(src).tokenize()).parse())
        assert interp.runtime.pending_audio["fade_in"] == 2.0

    def test_stop_music_with_fade(self):
        src = 'stop music with fade 3.0\n'
        interp = Interpreter(runtime=Runtime())
        interp.run(Parser(Lexer(src).tokenize()).parse())
        assert interp.runtime.pending_audio["fade_out"] == 3.0
