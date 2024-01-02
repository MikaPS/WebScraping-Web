from flask import Flask, render_template, request, make_response, jsonify
from WebScraping import handle_csv
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/call_function', methods=['GET'])
def call_function():
    has_headers = int(request.args.get('has_headers'))
    appliance_type = request.args.get('appliance')
    count_products = int(request.args.get('countproducts'))
    url = request.args.get('url')
    if (url[0:8] != "https://"): 
        return make_response(jsonify(["URLError", "URLError"]))
    data, result, title = handle_csv(url, appliance_type, count_products, True, has_headers)
    # save values to a file
    response = make_response(jsonify([data, result, title]))
    return response

if __name__ == '__main__':
    app.run(debug=True)
