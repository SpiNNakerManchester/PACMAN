# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import unittest
from pacman.executor.algorithm_decorators import Token
from pacman.executor.token_states import TokenStates


class TestTokenStates(unittest.TestCase):

    def test_union(self):
        token1 = Token("One")
        token2 = Token("Two")
        token3 = Token("Three")
        token3a = Token("Three", "a")
        token3b = Token("Three", "b")
        token3c = Token("Three", "c")
        token4 = Token("Four")
        token4a = Token("Four", "a")
        token4b = Token("Four", "b")
        token5 = Token("Five")
        token6 = Token("Five")

        tokens = TokenStates()
        tokens.track_token(token1)
        tokens.track_token(token2)
        tokens.track_token(token3a)
        tokens.track_token(token3b)
        tokens.track_token(token4a)
        tokens.track_token(token4b)
        tokens.process_output_token(token2)
        tokens.process_output_token(token3b)
        tokens.process_output_token(token4a)
        self.assertFalse(tokens.is_token_complete(token1))
        self.assertTrue(tokens.is_token_complete(token2))
        self.assertFalse(tokens.is_token_complete(token3))
        self.assertFalse(tokens.is_token_complete(token3a))
        self.assertTrue(tokens.is_token_complete(token3b))
        self.assertFalse(tokens.is_token_complete(token3c))
        self.assertFalse(tokens.is_token_complete(token4))
        self.assertFalse(tokens.is_token_complete(token5))
        self.assertFalse(tokens.is_token_complete(token6))

        fake_tokens = TokenStates()
        fake_tokens.track_token(token1)
        fake_tokens.track_token(token5)
        fake_tokens.track_token(token3b)
        fake_tokens.track_token(token3c)
        fake_tokens.track_token(token4a)
        fake_tokens.track_token(token4b)
        fake_tokens.process_output_token(token1)
        fake_tokens.process_output_token(token3c)
        fake_tokens.process_output_token(token4b)
        fake_tokens.track_token(token5)
        self.assertTrue(fake_tokens.is_token_complete(token1))
        self.assertFalse(fake_tokens.is_token_complete(token2))
        self.assertFalse(fake_tokens.is_token_complete(token3))
        self.assertFalse(fake_tokens.is_token_complete(token3a))
        self.assertFalse(fake_tokens.is_token_complete(token3b))
        self.assertTrue(fake_tokens.is_token_complete(token3c))
        self.assertFalse(fake_tokens.is_token_complete(token4))
        self.assertFalse(fake_tokens.is_token_complete(token5))
        self.assertFalse(fake_tokens.is_token_complete(token6))

        the_tokens = tokens | fake_tokens
        self.assertTrue(the_tokens.is_token_complete(token1))
        self.assertTrue(the_tokens.is_token_complete(token2))
        self.assertFalse(the_tokens.is_token_complete(token3))
        self.assertFalse(the_tokens.is_token_complete(token3a))
        self.assertTrue(the_tokens.is_token_complete(token3b))
        self.assertTrue(the_tokens.is_token_complete(token3c))
        self.assertTrue(the_tokens.is_token_complete(token4))
        self.assertFalse(the_tokens.is_token_complete(token5))
        self.assertFalse(the_tokens.is_token_complete(token6))
