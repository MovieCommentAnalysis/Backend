import nltk
nltk.download('punkt')
import nltk
nltk.download('stopwords')

import os
from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv
from flask_mysqldb import MySQL
from flask_cors import CORS
from matplotlib import pyplot as plt
from wordcloud import WordCloud
from textblob import TextBlob
import seaborn as sns
import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

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
    name = request.json['name']
    content = request.json['content']
    movieId = request.json['movieId']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO comment (name, content, movieId) VALUES (%s, %s, %s)", (name, content, movieId))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': '留言新增成功'})

# 生成單一電影文字雲
@app.route('/movie/wordcloud/<int:movie_id>', methods=['GET'])
def generate_wordcloud(movie_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT content FROM comment WHERE movieId = %s", (movie_id,))
    comments = cur.fetchall()
    cur.close()

    text = ' '.join([comment[0] for comment in comments])
    font_path = os.path.join(os.path.dirname(__file__), 'truetype', 'Roboto-Black.ttf')
    wordcloud = WordCloud(width=800, height=400, background_color='white', font_path=font_path).generate(text)
    
     # 确保静態存在
    directory = os.path.join(os.path.dirname(__file__), 'static', 'wordclouds')
    if not os.path.exists(directory):
        os.makedirs(directory)

    # 保存圖像文件
    file_path = os.path.join(directory, f'wordcloud_{movie_id}.png')
    wordcloud.to_file(file_path)

    # 返回圖像的URL
    return jsonify({'image_url': f'/static/wordclouds/wordcloud_{movie_id}.png'})

# 分析單一電影所有留言的情緒
@app.route('/movie/sentiment/<int:movie_id>', methods=['GET'])
def analyze_movie_sentiment(movie_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT content FROM comment WHERE movieId = %s", (movie_id,))
    comments = cur.fetchall()
    cur.close()

    polarities = []
    subjectivities = []

    for comment in comments:
        # 預處理文本
        text = comment[0]
        text = text.lower()  # 轉換為小寫
        text = re.sub(r'[^\w\s]', '', text)  # 移除標點符號

        # 分詞
        words = word_tokenize(text)

        # 移除停用詞和過短詞語
        stop_words = set(stopwords.words('english'))
        words = [word for word in words if word not in stop_words and len(word) > 2]

        # 重建無停用詞的留言
        filtered_text = ' '.join(words)

        analysis = TextBlob(filtered_text)
        sentiment = analysis.sentiment
        polarities.append(sentiment.polarity)
        subjectivities.append(sentiment.subjectivity)

    avg_polarity = sum(polarities) / len(polarities) if polarities else 0
    avg_subjectivity = sum(subjectivities) / len(subjectivities) if subjectivities else 0

    # 生成主觀性圖表
    plt.figure(figsize=(10, 6))
    sns.kdeplot(subjectivities, fill=True, color='skyblue')
    plt.xlabel('Subjectivity')
    plt.ylabel('Density')
    plt.title('Kernel Density Estimate of Subjectivity Distribution for Movie ID {}'.format(movie_id))

    # 確保靜態文件夾存在
    directory = os.path.join(os.path.dirname(__file__), 'static', 'subjectivity_charts')
    if not os.path.exists(directory):
        os.makedirs(directory)

    # 保存圖表文件
    file_path = os.path.join(directory, f'subjectivity_chart_{movie_id}.png')
    plt.savefig(file_path)
    plt.close()
    
    # 生成情感性圖表
    plt.figure(figsize=(10, 6))
    sns.kdeplot(polarities, fill=True, color='orange')
    plt.xlabel('Polarity')
    plt.ylabel('Density')
    plt.title('Kernel Density Estimate of Polarity Distribution for Movie ID {}'.format(movie_id))

    # 確保靜態文件夾存在
    directory = os.path.join(os.path.dirname(__file__), 'static', 'polarity_charts')
    if not os.path.exists(directory):
        os.makedirs(directory)

    # 保存圖表文件
    file_path = os.path.join(directory, f'polarity_charts_{movie_id}.png')
    plt.savefig(file_path)
    plt.close()

    return jsonify({
        'average_polarity': avg_polarity,
        'average_subjectivity': avg_subjectivity,
        'subjectivity_chart_url': f'/static/subjectivity_charts/subjectivity_chart_{movie_id}.png',
        'polarity_charts_url': f'/static/polarity_charts/polarity_charts_{movie_id}.png'
    })

# 提供靜態文件訪問
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static/wordclouds', filename)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
