## Полная схема вызовов (по шагам)

```
1. Пользователь открывает http://localhost:5000
   ↓
2. Flask вызывает функцию index()
   ↓
3. index() проверяет current_user.is_authenticated → False
   ↓
4. index() возвращает HTML с ссылкой "/login/google"
   ↓
5. Пользователь нажимает ссылку → браузер идёт на /login/google
   ↓
6. Flask-Dance перенаправляет на Google (вы не видите этот код, он внутри библиотеки)
   ↓
7. Пользователь вводит логин/пароль на странице Google
   ↓
8. Google перенаправляет обратно на /login/google/authorized?code=...
   ↓
9. Flask-Dance перехватывает этот запрос и генерирует событие oauth_authorized
   ↓
10. Срабатывает декоратор @oauth_authorized.connect_via(google_bp)
    ↓
11. Вызывается функция google_logged_in(blueprint, token)
    ↓
12. Функция получает данные пользователя от Google
    ↓
13. Сохраняет пользователя в SQLite (если новый)
    ↓
14. Вызывает login_user(user) — Flask-Login создаёт сессию
    ↓
15. Возвращает True → Flask-Dance продолжает обработку
    ↓
16. Flask-Dance перенаправляет на главную страницу "/"
    ↓
17. Снова вызывается index(), но теперь current_user.is_authenticated → True
    ↓
18. index() возвращает HTML с приветствием
```

---

## Что что вызвало (причинно-следственные связи)

| Что произошло | Что это вызвало | Как связано |
|---------------|----------------|-------------|
| Пользователь нажал "Войти" | Браузер перешёл на `/login/google` | Клик → HTTP GET |
| Flask-Dance получил запрос на `/login/google` | Перенаправление на Google | Внутренняя логика библиотеки |
| Google вернул `code` на `/login/google/authorized` | Flask-Dance сгенерировал событие | OAuth 2.0 протокол |
| Событие `oauth_authorized` | Вызвалась `google_logged_in()` | Сигнал Flask-Dance |
| `google_logged_in()` получила токен | Запрос к Google API за userinfo | `blueprint.session.get(...)` |
| `login_user(user)` | Сохранился user_id в сессии Flask | Flask-Login |
| Возврат `True` | Flask-Dance перенаправил на `/` | Стандартное поведение |
| Запрос на `/` | Вызвалась `index()` | Маршрут Flask |
| `current_user.is_authenticated` → True | Показалось приветствие | Flask-Login загрузил пользователя |

---

## Ключевые точки в вашем коде с пояснениями

### 1. Декоратор `@oauth_authorized.connect_via(google_bp)`

```python
@oauth_authorized.connect_via(google_bp)
def google_logged_in(blueprint, token):
```

**Что делает:** Подписывается на сигнал Flask-Dance. Когда происходит успешная авторизация через Google, эта функция вызывается **автоматически**.

**Что такое сигнал:** Механизм Flask-Dance, который позволяет выполнить ваш код в момент, когда библиотека получила токен от Google.

### 2. `blueprint.session.get("/oauth2/v2/userinfo")`

```python
resp = blueprint.session.get("/oauth2/v2/userinfo")
```

**Что делает:** Отправляет HTTP GET запрос к Google API для получения информации о пользователе. Использует тот же сессию, где уже есть `access_token`.

### 3. `login_user(user, remember=True)`

```python
login_user(user, remember=True)
```

**Что делает:** Flask-Login сохраняет `user.id` в сессии. После этого `current_user` будет содержать этого пользователя в любом маршруте.

### 4. Возврат `True`

```python
return True
```

**Что делает:** Говорит Flask-Dance: "Всё хорошо, продолжай обработку". Flask-Dance после этого перенаправляет пользователя на страницу, указанную в `login_manager.login_view` (в вашем случае `"google.login"`), но обычно на `/`.

---

## Что происходит в Flask-Dance "под капотом" (код библиотеки)

Хотя вы этого не пишете, внутри библиотеки есть что-то вроде:

```python
# Внутри flask_dance/contrib/google.py (упрощённо)

@blueprint.route("/authorized")
def authorized():
    # Google вернул code в URL
    code = request.args.get("code")
    
    # Обмениваем code на token
    token = fetch_token(code=code)
    
    # Отправляем сигнал о получении токена
    oauth_authorized.send(blueprint, token=token)
    
    # Если обработчики сигнала вернули False - ошибка
    # Иначе перенаправляем на главную
    return redirect("/")
```

---

## Как увидеть реальную последовательность

Добавьте в ваш код отладочные принты:

```python
print("1. Пользователь зашёл на /")
print("2. Проверка авторизации")
print("3. Показываем ссылку входа")

@oauth_authorized.connect_via(google_bp)
def google_logged_in(blueprint, token):
    print("4. Сработал сигнал авторизации!")
    print("5. Получаем данные от Google")
    # ...
    print("6. Вызываем login_user()")
    login_user(user, remember=True)
    print("7. Возвращаем True")
    return True

@app.route("/")
def index():
    print("8. Снова вызвалась index()")
    if current_user.is_authenticated:
        print("9. Пользователь авторизован, показываем приветствие")
    else:
        print("Пользователь не авторизован")
```

---

## Триггеры (что инициирует каждый шаг)

| Шаг | Триггер (что запускает) |
|-----|------------------------|
| Запрос на `/` | Пользователь открыл страницу |
| Запрос на `/login/google` | Пользователь нажал ссылку |
| Редирект на Google | HTTP 302 ответ от Flask-Dance |
| Вызов `google_logged_in()` | Сигнал `oauth_authorized` |
| Запрос к Google API | `blueprint.session.get(...)` |
| Вызов `login_user()` | Ваш код внутри `google_logged_in()` |
| Редирект на `/` | Flask-Dance после успешного обработчика |
| Повторный вызов `index()` | HTTP GET запрос браузера |

---

## Итоговая цепочка вызовов

```
index() → (пользователь нажимает ссылку) 
→ google.login (Flask-Dance) 
→ Google OAuth сервер 
→ google.authorized (Flask-Dance) 
→ oauth_authorized сигнал 
→ google_logged_in() 
→ login_user() 
→ редирект на / 
→ index() с current_user
```

Вся магия в том, что **Flask-Dance и Flask-Login работают вместе**: первый получает токен от Google и генерирует сигнал, второй управляет сессией после вызова `login_user()`.