import requests
from bs4 import BeautifulSoup
import argparse
import urllib3
from urllib3.exceptions import InsecureRequestWarning

# DESATIVA AVISOS SSL (TEMPORÁRIO)
urllib3.disable_warnings(InsecureRequestWarning)

def detect_wordpress_info(url, verify_ssl=True):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(
            url,
            timeout=15,
            headers=headers,
            verify=verify_ssl
        )
        response.raise_for_status()
    except requests.exceptions.SSLError as e:
        if verify_ssl:
            print("⚠️ Tentando sem verificação SSL...")
            return detect_wordpress_info(url, verify_ssl=False)
        return {"error": f"Erro SSL crítico: {str(e)}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Erro na requisição: {str(e)}"}

    soup = BeautifulSoup(response.text, 'html.parser')
    themes = set()
    plugins = set()
    wp_version = "Desconhecida"

    # Detecção aprimorada de temas
    try:
        # Via links de CSS/JS
        for link in soup.find_all('link', href=True):
            href = link['href']
            if '/wp-content/themes/' in href:
                theme_name = href.split('/themes/')[-1].split('/')[0]
                themes.add(theme_name)
        
        # Via classes do body (com verificação de existência)
        body_tag = soup.find('body', class_=True)
        if body_tag:
            body_classes = body_tag.get('class', [])
            for cls in body_classes:
                if cls.startswith('theme-'):
                    themes.add(cls.replace('theme-', ''))
    except Exception as e:
        return {"error": f"Erro na detecção de temas: {str(e)}"}

    # Detecção de plugins
    try:
        for tag in soup.find_all(['script', 'link'], src=True):
            src = tag['src']
            if '/wp-content/plugins/' in src:
                plugin_name = src.split('/plugins/')[-1].split('/')[0]
                plugins.add(plugin_name)
    except Exception as e:
        return {"error": f"Erro na detecção de plugins: {str(e)}"}

    # Detecção de versão
    try:
        meta_generator = soup.find('meta', {'name': 'generator'})
        if meta_generator and 'WordPress' in meta_generator.get('content', ''):
            wp_version = meta_generator['content'].split(' ')[1]
    except Exception as e:
        return {"error": f"Erro na detecção de versão: {str(e)}"}

    return {
        'themes': themes,
        'plugins': plugins,
        'wp_version': wp_version
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Detector de temas/plugins WordPress")
    parser.add_argument("url", help="URL do site WordPress")
    parser.add_argument("--insecure", action="store_true", 
                      help="Ignorar verificação SSL (USE COM CAUTELA)")
    args = parser.parse_args()

    result = detect_wordpress_info(args.url, verify_ssl=not args.insecure)
    
    if 'error' in result:
        print(f"❌ Erro: {result['error']}")
    else:
        print(f"✅ Informações detectadas em {args.url}:")
        print(f"\n🎨 Temas ({len(result['themes'])} encontrado(s)):")
        for theme in sorted(result['themes']):
            print(f"- {theme}")
        print(f"\n🔌 Plugins ({len(result['plugins'])} encontrado(s)):") 
        for plugin in sorted(result['plugins']):
            print(f"- {plugin}")
        print(f"\nWordPress v{result['wp_version']}")
