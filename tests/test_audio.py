import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.lexer import Lexer
from core.parser import Parser
from core.interpreter import Interpreter
from core.runtime import Runtime
from core.ast import PlayMusicStmt, PlaySoundStmt, StopMusicStmt, StopSoundStmt, SetVolumeStmt


class TestAudioLexer:
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
        assert stmt.sound_volume == -1.0

    def test_volume_sound(self):
        program = self.parse('volume sound = 0.5')
        stmt = program.statements[0]
        assert isinstance(stmt, SetVolumeStmt)
        assert stmt.sound_volume == 0.5
        assert stmt.music_volume == -1.0

    def test_music_in_label(self):
        src = '''
label start:
    music "bgm.mp3"
    sound "sfx.wav"
end
'''
        program = self.parse(src)
        stmt = program.statements[0]
        assert len(stmt.body) == 2
        assert isinstance(stmt.body[0], PlayMusicStmt)
        assert isinstance(stmt.body[1], PlaySoundStmt)


class TestAudioInterpreter:
    def run(self, src: str):
        tokens = Lexer(src).tokenize()
        program = Parser(tokens).parse()
        interp = Interpreter(runtime=Runtime())
        interp.run(program)
        return interp

    def test_play_music_sets_pending_audio(self):
        src = '''
label start:
    music "bgm.mp3"
end
'''
        interp = self.run(src)
        assert interp.runtime.pending_audio is not None
        assert interp.runtime.pending_audio["type"] == "play_music"
        assert interp.runtime.pending_audio["path"] == "bgm.mp3"

    def test_play_sound_sets_pending_audio(self):
        src = '''
label start:
    sound "sfx.wav"
end
'''
        interp = self.run(src)
        assert interp.runtime.pending_audio is not None
        assert interp.runtime.pending_audio["type"] == "play_sound"
        assert interp.runtime.pending_audio["path"] == "sfx.wav"

    def test_stop_music_sets_pending_audio(self):
        src = '''
label start:
    stop music
end
'''
        interp = self.run(src)
        assert interp.runtime.pending_audio is not None
        assert interp.runtime.pending_audio["type"] == "stop_music"

    def test_stop_sound_sets_pending_audio(self):
        src = '''
label start:
    stop sound
end
'''
        interp = self.run(src)
        assert interp.runtime.pending_audio is not None
        assert interp.runtime.pending_audio["type"] == "stop_sound"

    def test_volume_music(self):
        src = '''
label start:
    volume music = 0.5
end
'''
        interp = self.run(src)
        assert interp.runtime.music_volume == 0.5
        assert interp.runtime.pending_audio is not None
        assert interp.runtime.pending_audio["type"] == "set_volume"
        assert interp.runtime.pending_audio["music_volume"] == 0.5

    def test_volume_sound(self):
        src = '''
label start:
    volume sound = 0.7
end
'''
        interp = self.run(src)
        assert interp.runtime.sound_volume == 0.7
        assert interp.runtime.pending_audio is not None
        assert interp.runtime.pending_audio["type"] == "set_volume"
        assert interp.runtime.pending_audio["sound_volume"] == 0.7

    def test_music_with_options(self):
        src = '''
label start:
    music "bgm.mp3" volume 0.6
end
'''
        interp = self.run(src)
        assert interp.runtime.pending_audio["volume"] == 0.6

    def test_music_with_fade(self):
        src = '''
label start:
    music "bgm.mp3" with fade 2.0
end
'''
        interp = self.run(src)
        assert interp.runtime.pending_audio["fade_in"] == 2.0

    def test_stop_music_with_fade(self):
        src = '''
label start:
    stop music with fade 3.0
end
'''
        interp = self.run(src)
        assert interp.runtime.pending_audio["fade_out"] == 3.0
