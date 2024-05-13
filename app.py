import os
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from flask_mysqldb import MySQL
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

load_dotenv()
print(os.getenv('DB_PORT'))

# 設置資料庫連接設置
app.config['MYSQL_HOST'] = os.getenv('DB_HOST')
app.config['MYSQL_PORT'] = int(os.getenv('DB_PORT'))
app.config['MYSQL_USER'] = os.getenv('ROOT_USERNAME')
app.config['MYSQL_PASSWORD'] = os.getenv('ROOT_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('DB_DATABASE')

# 初始化MySQL
mysql = MySQL(app)

# 獲取所有電影
@app.route('/movies', methods=['GET'])
def get_movies():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM movie")
    movies = cur.fetchall()
    cur.close()
    return jsonify({'movies': movies})

# 新增單一電影
@app.route('/movie', methods=['POST'])
def add_movie():
    name = request.json['name']
    introduction = request.json['introduction']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO movie (name, introduction) VALUES (%s, %s)", (name, introduction))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': '電影新增成功'})

# 獲取單一電影所有留言
@app.route('/movie/comments/<int:movie_id>', methods=['GET'])
def get_movie_comments(movie_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM comment WHERE movieId = %s", (movie_id,))
    comments = cur.fetchall()
    cur.close()
    return jsonify({'comments': comments})

# 新增留言
@app.route('/comment', methods=['POST'])
def add_comment():
    userName = request.json['userName']
    content = request.json['content']
    movieId = request.json['movieId']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO comment (userName, content, movieId) VALUES (%s, %s, %s)", (userName, content, movieId))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': '留言新增成功'})

# 生成單一電影文字雲
# @app.route('/movie/wordcloud/<int:movie_id>', methods=['GET'])
# def generate_wordcloud(movie_id):
#     cur = mysql.connection.cursor()
#     cur.execute("SELECT content FROM comment WHERE movieId = %s", (movie_id,))
#     comments = cur.fetchall()
#     cur.close()

#     text = ' '.join([comment[0] for comment in comments])
#     font_path = "C:/Users/rumin/Downloads/web/Backend/truetype/Roboto-Black.ttf"
#     wordcloud = WordCloud(width=800, height=400, background_color='white', font_path = font_path).generate(text)

#     directory = "C:/Users/rumin/Downloads/web/Backend/static/"
#     if not os.path.exists(directory):
#         os.makedirs(directory)

#     wordcloud.to_file(os.path.join(directory, 'wordcloud.png'))
#     with open("C:/Users/rumin/Downloads/web/Backend/static/wordcloud.png", "rb") as image_file:
#         encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
#     return jsonify({'image': encoded_string})

if __name__ == '__main__':
    app.run(debug=True)
