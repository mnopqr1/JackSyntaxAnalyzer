from jacktokenizer import JackTokenizer
from jacktoken import Token

tokenizer = JackTokenizer("Main.jack")
while tokenizer.has_more_tokens():
    tokenizer.advance()
    print (tokenizer.current_token.to_string())

