import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException

def main():
    # --- URL NASLOVI ---
    BASE_URL_PRODUCTS = "https://web-scraping.dev/products"
    BASE_URL_REVIEWS = "https://web-scraping.dev/reviews"
    BASE_URL_TESTIMONIALS = "https://web-scraping.dev/testimonials"

    print("Zaganjam brskalnik...")
    driver = webdriver.Chrome()
    driver.maximize_window()
    wait = WebDriverWait(driver, 10)

    # Seznami za shranjevanje
    all_products = []
    all_reviews = []
    all_testimonials = []

    try:
# =================================================================
        # 1. DEL: PRODUKTI (ZANKA PO STRANEH)
        # =================================================================
        print(f"\n--- 1. Odpiram produkte: {BASE_URL_PRODUCTS} ---")
        driver.get(BASE_URL_PRODUCTS)
        
        page_num = 1
        while True:
            print(f"Obdelujem stran {page_num}...")

            try:
                # Počakamo na vrstice s produkti
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.row.product")))
                
                # Poiščemo vse kontejnerje produktov
                product_rows = driver.find_elements(By.CSS_SELECTOR, "div.row.product")
                
                for row in product_rows:
                    try:
                        # Iz vsake vrstice izvlečemo naslov in ceno
                        name = row.find_element(By.CSS_SELECTOR, "h3 a").text.strip()
                        price = row.find_element(By.CSS_SELECTOR, "div.price").text.strip()
                        
                        product_data = {
                            "name": name,
                            "price": price
                        }

                        # Preverimo, če produkt s tem imenom že obstaja v seznamu
                        if not any(p['name'] == name for p in all_products):
                            all_products.append(product_data)
                            
                    except Exception as e:
                        print(f"Napaka pri branju vrstice: {e}")
                        continue

            except TimeoutException:
                print("-> Na tej strani ni (več) produktov. Konec iskanja.")
                break

            print(f"-> Skupaj zbranih: {len(all_products)} produktov.")

            # C) KLIK NA NASLEDNJO STRAN
            try:
                # Iščemo gumb '>' znotraj paging razdelka
                next_button = driver.find_elements(By.CSS_SELECTOR, "div.paging a:last-child")
                
                if next_button and ">" in next_button[0].text:
                    btn = next_button[0]
                    
                    if "disabled" in btn.get_attribute("class"):
                        break

                    old_url = driver.current_url
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(2)
                    
                    if driver.current_url == old_url:
                        break
                    page_num += 1
                else:
                    break
            except:
                break

    # =================================================================
        # 2. DEL: REVIEWS
        # =================================================================
        print(f"\n--- 2. Prehajam na REVIEWJE: {BASE_URL_REVIEWS} ---")
        driver.get(BASE_URL_REVIEWS)
        
        try:
            # Kliknemo "Load More", da dobimo več podatkov
            for i in range(3): 
                try:
                    load_more = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Load More')]")))
                    driver.execute_script("arguments[0].click();", load_more)
                    time.sleep(1.5)
                except:
                    break 

            # Poiščemo elemente reviewjev
            review_elements = driver.find_elements(By.CSS_SELECTOR, ".review")
            
            for r in review_elements:
                full_text = r.text.strip()
                if full_text:
                    # Ločimo datum od besedila (split ob prvi novi vrstici)
                    parts = full_text.split('\n', 1)
                    
                    if len(parts) == 2:
                        date = parts[0].strip()
                        comment = parts[1].strip()
                    else:
                        # Če ni nove vrstice, damo vse pod komentar, datum pa pustimo prazen
                        date = "N/A"
                        comment = full_text
                    
                    all_reviews.append({
                        "date": date,
                        "comment": comment
                    })
            
            print(f"-> Uspešno shranil {len(all_reviews)} reviewjev.")

        except Exception as e:
            print(f"Napaka pri reviewjih: {e}")

        # =================================================================
        # 3. DEL: TESTIMONIALS
        # =================================================================
        print(f"\n--- 3. Prehajam na TESTIMONIALS: {BASE_URL_TESTIMONIALS} ---")
        driver.get(BASE_URL_TESTIMONIALS)

        try:
            print("Izvajam scroll na dno strani...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2) 
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            testimonials = wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, ".testimonial-item, .testimonial")
            ))
            for t in testimonials:
                txt = t.text.strip()
                if txt:
                    all_testimonials.append(txt[:50] + "...")
            
            print(f"-> Uspešno shranil {len(testimonials)} testimonialsov.")

        except TimeoutException:
            print("Nisem našel nobenega testimonialsa.")

    except Exception as e:
        print(f"KRITIČNA NAPAKA: {e}")

    finally:
        # =================================================================
        # SHRANJEVANJE IN KONEC
        # =================================================================
        print("\n=== SHRANJUJEM PODATKE V JSON ===")
        
        data_to_save = {
            "products": all_products,
            "reviews": all_reviews,
            "testimonials": all_testimonials
        }

        try:
            with open('data.json', 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)
            print("USPEH: Podatki shranjeni v 'data.json'.")
        except Exception as e:
            print(f"NAPAKA pri shranjevanju: {e}")

        print(f"Skupaj najdenih produktov: {len(all_products)}")
        print("Zapiram brskalnik...")
        driver.quit()

if __name__ == "__main__":
    main()