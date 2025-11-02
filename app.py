from flask import Flask, render_template\

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/Mobile')
def mobile():
    return render_template('mobile.html')

@app.route('/Laptop')
def laptop():
    return render_template('laptop.html')

@app.route('/TV')
def tv():
    return render_template('tv.html')

@app.route('/Sound System')
def ss():
    return render_template('ss.html')

@app.route('/cart')
def account():
    return render_template('account.html')


if __name__ == '__main__':
    app.run(debug=True)