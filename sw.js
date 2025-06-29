// ===================================================================
// SERVICE WORKER BÁSICO - Sistema de Crediário
// ===================================================================

const CACHE_NAME = 'acougue-sistema-v1.0.0';
const urlsToCache = [
    '/',
    '/static/css/style.css',
    '/static/js/main.js',
    '/static/img/logo.png',
    // Adicione outros recursos estáticos que quer cachear
];

// ===================================================================
// INSTALAÇÃO DO SERVICE WORKER
// ===================================================================
self.addEventListener('install', event => {
    console.log('Service Worker: Instalando...');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Service Worker: Cache aberto');
                return cache.addAll(urlsToCache);
            })
            .catch(error => {
                console.error('Service Worker: Erro ao cachear:', error);
            })
    );
});

// ===================================================================
// ATIVAÇÃO DO SERVICE WORKER
// ===================================================================
self.addEventListener('activate', event => {
    console.log('Service Worker: Ativado');
    
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    // Remover caches antigos
                    if (cacheName !== CACHE_NAME) {
                        console.log('Service Worker: Removendo cache antigo:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// ===================================================================
// INTERCEPTAÇÃO DE REQUISIÇÕES (ESTRATÉGIA CACHE FIRST)
// ===================================================================
self.addEventListener('fetch', event => {
    // Só cachear GET requests
    if (event.request.method !== 'GET') {
        return;
    }
    
    // Não cachear requisições da API (para manter dados atualizados)
    if (event.request.url.includes('/api/')) {
        return;
    }
    
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                // Se encontrou no cache, retornar
                if (response) {
                    console.log('Service Worker: Servindo do cache:', event.request.url);
                    return response;
                }
                
                // Senão, buscar da rede
                return fetch(event.request)
                    .then(response => {
                        // Verificar se é uma resposta válida
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }
                        
                        // Clonar a resposta para cachear
                        const responseToCache = response.clone();
                        
                        caches.open(CACHE_NAME)
                            .then(cache => {
                                cache.put(event.request, responseToCache);
                            });
                        
                        return response;
                    })
                    .catch(error => {
                        console.error('Service Worker: Erro na requisição:', error);
                        
                        // Retornar página offline personalizada se houver
                        if (event.request.destination === 'document') {
                            return caches.match('/offline.html');
                        }
                    });
            })
    );
});

// ===================================================================
// LIMPEZA PERIÓDICA DO CACHE
// ===================================================================
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'CLEAR_CACHE') {
        event.waitUntil(
            caches.keys().then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => caches.delete(cacheName))
                );
            }).then(() => {
                event.ports[0].postMessage({success: true});
            })
        );
    }
});

console.log('Service Worker: Carregado com sucesso!');