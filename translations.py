"""
Translation module for Web Sherlock application
"""

TRANSLATIONS = {
    'pt': {
        # Page titles and headers
        'app_title': 'Web Sherlock',
        'app_subtitle': 'Interface Web para buscar usuários com Sherlock',
        'search_results': 'Resultados da Busca',
        
        # Navigation
        'home': 'Início',
        'results': 'Resultados',
        'language': 'Idioma',
        
        # Form labels and placeholders
        'usernames_label': 'Nomes de usuário',
        'usernames_placeholder': 'Digite um ou mais nomes de usuário (um por linha)',
        'json_upload_label': 'Ou faça upload de um arquivo JSON',
        'search_options': 'Opções de Busca',
        'export_options': 'Opções de Exportação',
        'network_options': 'Opções de Rede',
        'timeout_label': 'Timeout (segundos)',
        'proxy_label': 'Servidor Proxy',
        'proxy_placeholder': 'Ex: http://proxy.exemplo.com:8080',
        
        # Buttons
        'start_search': 'Iniciar Busca',
        'export_csv': 'Exportar CSV',
        'export_json': 'Exportar JSON',
        'export_pdf': 'Exportar PDF',
        'export_txt': 'Exportar TXT',
        'download_all': 'Baixar Tudo (ZIP)',
        'new_search': 'Nova Busca',
        
        # Search options
        'verbose': 'Modo detalhado (--verbose)',
        'tor': 'Usar Tor (--tor)',
        'unique_tor': 'Tor único por site (--unique-tor)',
        'csv': 'Salvar em CSV (--csv)',
        'xlsx': 'Salvar em Excel (--xlsx)',
        'json': 'Salvar em JSON (--json)',
        'print_all': 'Mostrar todos os sites (--print-all)',
        'print_found': 'Mostrar apenas encontrados (--print-found)',
        'no_color': 'Sem cores (--no-color)',
        'browse': 'Abrir no navegador (--browse)',
        'nsfw': 'Incluir sites NSFW (--nsfw)',
        'local': 'Usar dados locais (--local)',
        
        # Table headers
        'username': 'Nome de usuário',
        'social_network': 'Rede Social',
        'profile_url': 'URL do Perfil',
        'status': 'Status',
        'response_time': 'Tempo de Resposta',
        
        # Status messages
        'found': 'Encontrado',
        'not_found': 'Não encontrado',
        'searching': 'Buscando...',
        'search_starting': 'Iniciando busca...',
        'search_completed': 'Busca concluída!',
        'searching_user': 'Buscando usuário',
        'processing_results': 'Processando resultados...',
        
        # Statistics
        'timestamp': 'Data/Hora',
        'usernames_searched': 'Usuários pesquisados',
        'profiles_found': 'Perfis encontrados',
        'profiles_not_found': 'Perfis não encontrados',
        'total_sites_checked': 'Total de sites verificados',
        'found_profiles': 'Perfis Encontrados',
        'not_found_profiles': 'Perfis Não Encontrados',
        
        # Error messages
        'error_no_usernames': 'Por favor, insira pelo menos um nome de usuário.',
        'error_invalid_json': 'Arquivo JSON inválido.',
        'error_sherlock_not_found': 'Sherlock não encontrado. Verifique a instalação.',
        'error_search_failed': 'Falha na busca. Tente novamente.',
        'error_export_failed': 'Falha na exportação.',
        'error_404': 'Página não encontrada.',
        'error_500': 'Erro interno do servidor.',
        

        
        # Help text
        'help_usernames': 'Digite um nome de usuário por linha. Você pode pesquisar múltiplos usuários ao mesmo tempo.',
        'help_json': 'Faça upload de um arquivo JSON contendo uma lista de nomes de usuário.',
        'help_timeout': 'Tempo limite em segundos para cada requisição (padrão: 60).',
        'help_proxy': 'Servidor proxy para usar nas requisições (formato: http://proxy:porta).',
    },
    
    'en': {
        # Page titles and headers
        'app_title': 'Web Sherlock',
        'app_subtitle': 'Web Interface for searching users with Sherlock',
        'search_results': 'Search Results',
        
        # Navigation
        'home': 'Home',
        'results': 'Results',
        'language': 'Language',
        
        # Form labels and placeholders
        'usernames_label': 'Usernames',
        'usernames_placeholder': 'Enter one or more usernames (one per line)',
        'json_upload_label': 'Or upload a JSON file',
        'search_options': 'Search Options',
        'export_options': 'Export Options',
        'network_options': 'Network Options',
        'timeout_label': 'Timeout (seconds)',
        'proxy_label': 'Proxy Server',
        'proxy_placeholder': 'Ex: http://proxy.example.com:8080',
        
        # Buttons
        'start_search': 'Start Search',
        'export_csv': 'Export CSV',
        'export_json': 'Export JSON',
        'export_pdf': 'Export PDF',
        'export_txt': 'Export TXT',
        'download_all': 'Download All (ZIP)',
        'new_search': 'New Search',
        
        # Search options
        'verbose': 'Verbose mode (--verbose)',
        'tor': 'Use Tor (--tor)',
        'unique_tor': 'Unique Tor per site (--unique-tor)',
        'csv': 'Save to CSV (--csv)',
        'xlsx': 'Save to Excel (--xlsx)',
        'json': 'Save to JSON (--json)',
        'print_all': 'Show all sites (--print-all)',
        'print_found': 'Show only found (--print-found)',
        'no_color': 'No colors (--no-color)',
        'browse': 'Open in browser (--browse)',
        'nsfw': 'Include NSFW sites (--nsfw)',
        'local': 'Use local data (--local)',
        
        # Table headers
        'username': 'Username',
        'social_network': 'Social Network',
        'profile_url': 'Profile URL',
        'status': 'Status',
        'response_time': 'Response Time',
        
        # Status messages
        'found': 'Found',
        'not_found': 'Not found',
        'searching': 'Searching...',
        'search_starting': 'Starting search...',
        'search_completed': 'Search completed!',
        'searching_user': 'Searching user',
        'processing_results': 'Processing results...',
        
        # Statistics
        'timestamp': 'Timestamp',
        'usernames_searched': 'Usernames searched',
        'profiles_found': 'Profiles found',
        'profiles_not_found': 'Profiles not found',
        'total_sites_checked': 'Total sites checked',
        'found_profiles': 'Found Profiles',
        'not_found_profiles': 'Not Found Profiles',
        
        # Error messages
        'error_no_usernames': 'Please enter at least one username.',
        'error_invalid_json': 'Invalid JSON file.',
        'error_sherlock_not_found': 'Sherlock not found. Check installation.',
        'error_search_failed': 'Search failed. Please try again.',
        'error_export_failed': 'Export failed.',
        'error_404': 'Page not found.',
        'error_500': 'Internal server error.',
        

        
        # Help text
        'help_usernames': 'Enter one username per line. You can search multiple users at once.',
        'help_json': 'Upload a JSON file containing a list of usernames.',
        'help_timeout': 'Timeout in seconds for each request (default: 60).',
        'help_proxy': 'Proxy server to use for requests (format: http://proxy:port).',
    }
}

def get_translations(language='pt'):
    """Get translations for specified language"""
    return TRANSLATIONS.get(language, TRANSLATIONS['pt'])

def get_supported_languages():
    """Get list of supported language codes"""
    return list(TRANSLATIONS.keys())
