import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


options = webdriver.FirefoxOptions()
options.binary_location = r'C:\Program Files\Mozilla Firefox\firefox.exe'
driver = webdriver.Firefox(options=options)

data = []

for option in ['sii', 'otc', 'rotc', 'pub']:
    driver.get('https://mops.twse.com.tw/mops/web/t51sb03')
    
    wait = WebDriverWait(driver, 10)
    wait.until(EC.visibility_of_element_located((By.ID, 'year')))
    
    select_element = driver.find_element(By.ID, "TYPEK")
    driver.execute_script("arguments[0].setAttribute('type', 'text')", select_element)
    select_element.click()

    option_to_select = driver.find_element(By.XPATH, f"//option[@value='{option}']")
    option_to_select.click()
    
    year_input = driver.find_element(By.ID, "year")
    year_input.clear()
    year_input.send_keys("113")
    
    index_select = Select(driver.find_element(By.ID, "index"))
    index_select.select_by_value("2")
    
    driver.execute_script("doAction();ajax1(document.form1,'table01');")
    
    wait.until(EC.visibility_of_element_located((By.ID, 'table01')))
    
    html_content = driver.page_source
    soup = BeautifulSoup(html_content, 'html.parser')
    
    buttons = driver.find_elements(By.CSS_SELECTOR, "input[value='詳細資料']")
    print(len(buttons))
    tickers = []
    
    for cell in soup.find_all('td'):
        try:
            number = int(cell.text.strip())
            button = buttons[len(tickers)].click()
            tickers.append(number)
            
            wait.until(EC.number_of_windows_to_be(2))
            window_handles = driver.window_handles
            new_window_handle = window_handles[1]
            driver.switch_to.window(new_window_handle)
            
            wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'noBorder')))
            time.sleep(3)
            
            html_content = driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')
            center_tags = soup.find_all('td', {'align': 'center'})[1:]
            
            '''輸出成excel表為字符，若要全轉純數字可用此區塊 ex：100,000 → 100000
            soup = BeautifulSoup(html_content, 'html.parser')
            center_tags = soup.find_all('td', {'align': 'center'})[1:]
            for center_tag in center_tags:
                result = [center_tag.text.strip()] 
                for tag in center_tag.find_next_siblings()[:3]:
                    text = tag.text.strip()
                    if text.replace(',', '').isdigit():
                        result.append(int(text.replace(',', '')))
                    else:
                        result.append(text)
                result.insert(0, number)
                data.append(result)
            '''
            
            for center_tag in center_tags:
                result = [center_tag.text.strip()] + [tag.text.strip() for tag in center_tag.find_next_siblings()[:3]]
                result.insert(0, number)
                data.append(result)
        
            driver.close()
            driver.switch_to.window(window_handles[0])
        except ValueError:
            pass
        
    print(len(tickers), len(buttons))
    
df = pd.DataFrame(data, columns=['Ticker', '日期', '數額', '每單位價格', '發行金額'])
df.to_excel('mops_twse.xlsx', index=False)

driver.quit()
