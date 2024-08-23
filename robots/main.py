from RPA.Browser.Selenium import Selenium
from RPA.Excel.Files import Files

browser = Selenium()
excel = Files()

def open_website_and_search(phrase, category):
    browser.open_available_browser('https://www.reuters.com/')
    browser.input_text('input[name="q"]', phrase)
    browser.press_keys('input[name="q"]', 'ENTER')

def extract_news_data():
    # Aqui vai o código para extrair os dados
    pass

def save_to_excel(data):
    excel.create_workbook('output/news_data.xlsx')
    excel.append_rows_to_worksheet(data)
    excel.save_workbook()

def main():
    open_website_and_search('AI', 'Technology')
    data = extract_news_data()
    save_to_excel(data)

if __name__ == "__main__":
    main()
