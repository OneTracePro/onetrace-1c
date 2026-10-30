"""Заглушка API OneTrace для теста ядра в CI: /api/v1/key, /api/v1/batch, /api/v1/stores — как платформа.

Ключ — test-secret. В пакете сообщение без телефона, карты и email (или с телефоном без цифр) отклоняется так же, как
платформа: 422 и ошибка batch.<номер>.anonymousId для всего пакета. Тело с BOM — 400 (платформа не разберёт JSON).
Принятые запросы пишутся в файл из аргумента: тест сверяет их после прогона.
"""
import json
import re
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

KEY = 'test-secret'
LOG = sys.argv[2]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def authorized(self):
        if self.headers.get('Authorization') != f'Bearer {KEY}':
            self.reply(401, {'message': 'Неверный ключ API.'})
            return False
        return True

    def do_GET(self):
        if self.path == '/api/v1/key' and self.authorized():
            self.reply(200, {'type': 'secret', 'scopes': ['products.write']})

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        if raw.startswith(b'\xef\xbb\xbf'):
            self.reply(400, {'message': 'BOM'})
            return
        if not self.authorized():
            return
        body = json.loads(raw)
        with open(LOG, 'a', encoding='utf-8') as log:
            log.write(json.dumps({'path': self.path, 'body': body}, ensure_ascii=False) + '\n')
        if self.path == '/api/v1/batch':
            errors = {}
            for index, message in enumerate(body['batch']):
                traits = message.get('context', {}).get('traits', {})
                phone_ok = len(re.sub(r'\D', '', traits.get('phone', ''))) >= 10
                if not (phone_ok or traits.get('loyalty_card') or traits.get('email')):
                    errors[f'batch.{index}.anonymousId'] = ['Поле anonymousId обязательно для заполнения, когда userId не указано.']
            if errors:
                self.reply(422, {'message': 'Ошибка проверки.', 'errors': errors})
            else:
                self.reply(202, {'accepted': len(body['batch'])})
        elif self.path == '/api/v1/stores':
            self.reply(200, {'saved': len(body['items'])})
        else:
            self.reply(404, {'message': 'Not found'})


HTTPServer(('127.0.0.1', int(sys.argv[1])), Handler).serve_forever()
