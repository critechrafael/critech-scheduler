from flask import Flask, request, jsonify, render_template_string
import requests
import json
import os
from datetime import datetime
import threading
import time
import schedule

app = Flask(__name__)

# Configurações
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN', '')
INSTAGRAM_USER_ID = os.environ.get('INSTAGRAM_USER_ID', '17841459866694291')

# Armazenamento simples em memória (posts agendados)
scheduled_posts = []

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CriTech Scheduler</title>
    <link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --yellow: #F5C400;
            --black: #0a0a0a;
            --dark: #111111;
            --card: #1a1a1a;
            --border: #2a2a2a;
            --text: #ffffff;
            --muted: #888888;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            background: var(--black);
            color: var(--text);
            font-family: 'DM Sans', sans-serif;
            min-height: 100vh;
        }

        header {
            background: var(--dark);
            border-bottom: 1px solid var(--border);
            padding: 20px 40px;
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .logo {
            width: 42px;
            height: 42px;
            background: var(--yellow);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Syne', sans-serif;
            font-weight: 800;
            color: var(--black);
            font-size: 18px;
        }

        header h1 {
            font-family: 'Syne', sans-serif;
            font-weight: 700;
            font-size: 20px;
            color: var(--text);
        }

        header span {
            color: var(--yellow);
        }

        .badge {
            background: #1a2a1a;
            color: #4caf50;
            border: 1px solid #2a4a2a;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            margin-left: auto;
        }

        .container {
            max-width: 1100px;
            margin: 0 auto;
            padding: 40px 20px;
        }

        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
        }

        @media (max-width: 768px) {
            .grid { grid-template-columns: 1fr; }
            header { padding: 16px 20px; }
        }

        .card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 28px;
        }

        .card h2 {
            font-family: 'Syne', sans-serif;
            font-weight: 700;
            font-size: 18px;
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .card h2 .icon {
            width: 32px;
            height: 32px;
            background: var(--yellow);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
        }

        .tabs {
            display: flex;
            gap: 8px;
            margin-bottom: 24px;
        }

        .tab {
            padding: 8px 20px;
            border-radius: 8px;
            border: 1px solid var(--border);
            background: transparent;
            color: var(--muted);
            cursor: pointer;
            font-family: 'DM Sans', sans-serif;
            font-size: 14px;
            transition: all 0.2s;
        }

        .tab.active {
            background: var(--yellow);
            color: var(--black);
            border-color: var(--yellow);
            font-weight: 600;
        }

        .form-group {
            margin-bottom: 18px;
        }

        label {
            display: block;
            font-size: 13px;
            color: var(--muted);
            margin-bottom: 8px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        input, textarea, select {
            width: 100%;
            background: var(--black);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 12px 16px;
            color: var(--text);
            font-family: 'DM Sans', sans-serif;
            font-size: 14px;
            transition: border-color 0.2s;
            outline: none;
        }

        input:focus, textarea:focus, select:focus {
            border-color: var(--yellow);
        }

        textarea {
            resize: vertical;
            min-height: 100px;
        }

        select option {
            background: var(--dark);
        }

        .btn {
            width: 100%;
            padding: 14px;
            background: var(--yellow);
            color: var(--black);
            border: none;
            border-radius: 10px;
            font-family: 'Syne', sans-serif;
            font-weight: 700;
            font-size: 15px;
            cursor: pointer;
            transition: opacity 0.2s, transform 0.1s;
            margin-top: 8px;
        }

        .btn:hover { opacity: 0.9; transform: translateY(-1px); }
        .btn:active { transform: translateY(0); }

        .btn-secondary {
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text);
        }

        .btn-secondary:hover {
            border-color: var(--yellow);
            color: var(--yellow);
        }

        .preview-box {
            background: var(--black);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 16px;
            min-height: 120px;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--muted);
            font-size: 13px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }

        .preview-box img {
            max-width: 100%;
            max-height: 200px;
            border-radius: 8px;
            object-fit: cover;
        }

        .post-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .post-item {
            background: var(--black);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 14px 16px;
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .post-thumb {
            width: 48px;
            height: 48px;
            background: var(--border);
            border-radius: 8px;
            flex-shrink: 0;
            overflow: hidden;
        }

        .post-thumb img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .post-info {
            flex: 1;
            min-width: 0;
        }

        .post-caption {
            font-size: 13px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            margin-bottom: 4px;
        }

        .post-time {
            font-size: 11px;
            color: var(--muted);
        }

        .post-status {
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            flex-shrink: 0;
        }

        .status-pending {
            background: #1a1a00;
            color: var(--yellow);
            border: 1px solid #333300;
        }

        .status-published {
            background: #0a1a0a;
            color: #4caf50;
            border: 1px solid #1a3a1a;
        }

        .status-error {
            background: #1a0a0a;
            color: #f44336;
            border: 1px solid #3a1a1a;
        }

        .delete-btn {
            background: none;
            border: none;
            color: var(--muted);
            cursor: pointer;
            font-size: 16px;
            padding: 4px;
            transition: color 0.2s;
        }

        .delete-btn:hover { color: #f44336; }

        .alert {
            padding: 12px 16px;
            border-radius: 10px;
            font-size: 13px;
            margin-bottom: 16px;
            display: none;
        }

        .alert-success {
            background: #0a1a0a;
            color: #4caf50;
            border: 1px solid #1a3a1a;
        }

        .alert-error {
            background: #1a0a0a;
            color: #f44336;
            border: 1px solid #3a1a1a;
        }

        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: var(--muted);
        }

        .empty-state .emoji {
            font-size: 40px;
            margin-bottom: 12px;
        }

        .full-width {
            grid-column: 1 / -1;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }

        .stat {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }

        .stat-number {
            font-family: 'Syne', sans-serif;
            font-size: 28px;
            font-weight: 800;
            color: var(--yellow);
        }

        .stat-label {
            font-size: 12px;
            color: var(--muted);
            margin-top: 4px;
        }

        .type-selector {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 8px;
            margin-bottom: 18px;
        }

        .type-btn {
            padding: 10px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: transparent;
            color: var(--muted);
            cursor: pointer;
            font-size: 13px;
            transition: all 0.2s;
            text-align: center;
        }

        .type-btn.active {
            border-color: var(--yellow);
            color: var(--yellow);
            background: #1a1500;
        }

        .loading {
            opacity: 0.6;
            pointer-events: none;
        }
    </style>
</head>
<body>

<header>
    <div class="logo">CT</div>
    <h1>CriTech <span>Scheduler</span></h1>
    <div class="badge">● Instagram Conectado</div>
</header>

<div class="container">

    <div class="stats">
        <div class="stat">
            <div class="stat-number" id="stat-pending">0</div>
            <div class="stat-label">Agendados</div>
        </div>
        <div class="stat">
            <div class="stat-number" id="stat-published">0</div>
            <div class="stat-label">Publicados</div>
        </div>
        <div class="stat">
            <div class="stat-number" id="stat-total">0</div>
            <div class="stat-label">Total</div>
        </div>
    </div>

    <div class="grid">

        <!-- FORMULÁRIO -->
        <div class="card">
            <h2><div class="icon">✏️</div> Novo Post</h2>

            <div id="alert" class="alert"></div>

            <div class="type-selector">
                <button class="type-btn active" onclick="setType('feed', this)">📸 Feed</button>
                <button class="type-btn" onclick="setType('reels', this)">🎬 Reels</button>
                <button class="type-btn" onclick="setType('stories', this)">⭕ Stories</button>
            </div>

            <div class="form-group">
                <label>URL da Imagem/Vídeo *</label>
                <input type="url" id="media-url" placeholder="https://..." oninput="previewMedia(this.value)">
            </div>

            <div class="preview-box" id="preview">
                <span>Prévia aparecerá aqui</span>
            </div>

            <div class="form-group" id="caption-group">
                <label>Legenda</label>
                <textarea id="caption" placeholder="Escreva a legenda do post...&#10;&#10;Use # para hashtags e @ para menções"></textarea>
            </div>

            <div class="form-group">
                <label>Agendar para</label>
                <input type="datetime-local" id="schedule-time">
            </div>

            <button class="btn" onclick="schedulePost()">⚡ Agendar Post</button>
            <button class="btn btn-secondary" style="margin-top:10px" onclick="publishNow()">🚀 Publicar Agora</button>
        </div>

        <!-- LISTA -->
        <div class="card">
            <h2><div class="icon">📋</div> Posts Agendados</h2>

            <div id="posts-list" class="post-list">
                <div class="empty-state">
                    <div class="emoji">📭</div>
                    <p>Nenhum post agendado ainda</p>
                </div>
            </div>
        </div>

    </div>
</div>

<script>
    let postType = 'feed';
    let posts = [];

    function setType(type, btn) {
        postType = type;
        document.querySelectorAll('.type-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        // Stories não tem legenda
        document.getElementById('caption-group').style.display = type === 'stories' ? 'none' : 'block';
    }

    function previewMedia(url) {
        const box = document.getElementById('preview');
        if (!url) {
            box.innerHTML = '<span>Prévia aparecerá aqui</span>';
            return;
        }
        if (url.match(/\.(mp4|mov|avi)$/i)) {
            box.innerHTML = `<video src="${url}" style="max-width:100%;max-height:200px;border-radius:8px" controls></video>`;
        } else {
            box.innerHTML = `<img src="${url}" onerror="this.parentElement.innerHTML='<span>URL inválida ou imagem não carregou</span>'">`;
        }
    }

    function showAlert(msg, type) {
        const el = document.getElementById('alert');
        el.textContent = msg;
        el.className = `alert alert-${type}`;
        el.style.display = 'block';
        setTimeout(() => el.style.display = 'none', 5000);
    }

    async function schedulePost() {
        const url = document.getElementById('media-url').value;
        const caption = document.getElementById('caption').value;
        const scheduleTime = document.getElementById('schedule-time').value;

        if (!url) return showAlert('Insira a URL da mídia!', 'error');
        if (!scheduleTime) return showAlert('Escolha o horário de agendamento!', 'error');

        const btn = document.querySelector('.btn');
        btn.classList.add('loading');
        btn.textContent = 'Agendando...';

        try {
            const res = await fetch('/schedule', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    media_url: url,
                    caption: caption,
                    schedule_time: scheduleTime,
                    post_type: postType
                })
            });
            const data = await res.json();
            if (data.success) {
                showAlert('✅ Post agendado com sucesso!', 'success');
                document.getElementById('media-url').value = '';
                document.getElementById('caption').value = '';
                document.getElementById('schedule-time').value = '';
                document.getElementById('preview').innerHTML = '<span>Prévia aparecerá aqui</span>';
                loadPosts();
            } else {
                showAlert('Erro: ' + data.error, 'error');
            }
        } catch(e) {
            showAlert('Erro de conexão!', 'error');
        }

        btn.classList.remove('loading');
        btn.textContent = '⚡ Agendar Post';
    }

    async function publishNow() {
        const url = document.getElementById('media-url').value;
        const caption = document.getElementById('caption').value;

        if (!url) return showAlert('Insira a URL da mídia!', 'error');

        const btn = document.querySelectorAll('.btn')[1];
        btn.classList.add('loading');
        btn.textContent = 'Publicando...';

        try {
            const res = await fetch('/publish-now', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    media_url: url,
                    caption: caption,
                    post_type: postType
                })
            });
            const data = await res.json();
            if (data.success) {
                showAlert('🎉 Post publicado com sucesso no Instagram!', 'success');
                document.getElementById('media-url').value = '';
                document.getElementById('caption').value = '';
                document.getElementById('preview').innerHTML = '<span>Prévia aparecerá aqui</span>';
                loadPosts();
            } else {
                showAlert('Erro: ' + data.error, 'error');
            }
        } catch(e) {
            showAlert('Erro de conexão!', 'error');
        }

        btn.classList.remove('loading');
        btn.textContent = '🚀 Publicar Agora';
    }

    async function deletePost(id) {
        await fetch(`/delete/${id}`, {method: 'DELETE'});
        loadPosts();
    }

    async function loadPosts() {
        const res = await fetch('/posts');
        posts = await res.json();

        const pending = posts.filter(p => p.status === 'pending').length;
        const published = posts.filter(p => p.status === 'published').length;

        document.getElementById('stat-pending').textContent = pending;
        document.getElementById('stat-published').textContent = published;
        document.getElementById('stat-total').textContent = posts.length;

        const list = document.getElementById('posts-list');
        if (posts.length === 0) {
            list.innerHTML = '<div class="empty-state"><div class="emoji">📭</div><p>Nenhum post agendado ainda</p></div>';
            return;
        }

        list.innerHTML = posts.map(p => `
            <div class="post-item">
                <div class="post-thumb">
                    ${p.media_url ? `<img src="${p.media_url}" onerror="this.style.display='none'">` : ''}
                </div>
                <div class="post-info">
                    <div class="post-caption">${p.caption || '(sem legenda)'}</div>
                    <div class="post-time">${p.post_type.toUpperCase()} · ${p.schedule_time || 'Imediato'}</div>
                </div>
                <span class="post-status status-${p.status}">
                    ${p.status === 'pending' ? '⏳ Agendado' : p.status === 'published' ? '✅ Publicado' : '❌ Erro'}
                </span>
                <button class="delete-btn" onclick="deletePost(${p.id})">🗑️</button>
            </div>
        `).join('');
    }

    // Definir horário padrão (agora + 1h)
    const now = new Date();
    now.setHours(now.getHours() + 1);
    document.getElementById('schedule-time').value = now.toISOString().slice(0, 16);

    loadPosts();
    setInterval(loadPosts, 30000);
</script>

</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/posts', methods=['GET'])
def get_posts():
    return jsonify(scheduled_posts)

@app.route('/schedule', methods=['POST'])
def schedule_post():
    data = request.json
    post = {
        'id': len(scheduled_posts) + 1,
        'media_url': data.get('media_url'),
        'caption': data.get('caption', ''),
        'schedule_time': data.get('schedule_time'),
        'post_type': data.get('post_type', 'feed'),
        'status': 'pending',
        'created_at': datetime.now().isoformat()
    }
    scheduled_posts.append(post)
    return jsonify({'success': True, 'post': post})

@app.route('/publish-now', methods=['POST'])
def publish_now():
    data = request.json
    result = publish_to_instagram(
        data.get('media_url'),
        data.get('caption', ''),
        data.get('post_type', 'feed')
    )
    if result['success']:
        post = {
            'id': len(scheduled_posts) + 1,
            'media_url': data.get('media_url'),
            'caption': data.get('caption', ''),
            'schedule_time': None,
            'post_type': data.get('post_type', 'feed'),
            'status': 'published',
            'created_at': datetime.now().isoformat()
        }
        scheduled_posts.append(post)
    return jsonify(result)

@app.route('/delete/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    global scheduled_posts
    scheduled_posts = [p for p in scheduled_posts if p['id'] != post_id]
    return jsonify({'success': True})

def publish_to_instagram(media_url, caption, post_type):
    try:
        token = ACCESS_TOKEN
        user_id = INSTAGRAM_USER_ID

        if not token:
            return {'success': False, 'error': 'Token de acesso não configurado'}

        # Criar container de mídia
        if post_type == 'reels':
            container_data = {
                'media_type': 'REELS',
                'video_url': media_url,
                'caption': caption,
                'access_token': token
            }
        elif post_type == 'stories':
            # Verificar se é vídeo ou imagem
            if media_url.lower().endswith(('.mp4', '.mov')):
                container_data = {
                    'media_type': 'VIDEO',
                    'video_url': media_url,
                    'is_stories': True,
                    'access_token': token
                }
            else:
                container_data = {
                    'image_url': media_url,
                    'is_stories': True,
                    'access_token': token
                }
        else:
            container_data = {
                'image_url': media_url,
                'caption': caption,
                'access_token': token
            }

        # Step 1: criar container
        container_res = requests.post(
            f'https://graph.instagram.com/v21.0/{user_id}/media',
            data=container_data
        )
        container_json = container_res.json()

        if 'id' not in container_json:
            return {'success': False, 'error': str(container_json.get('error', {}).get('message', 'Erro ao criar container'))}

        container_id = container_json['id']

        # Para vídeos, aguardar processamento
        if post_type in ['reels'] or media_url.lower().endswith(('.mp4', '.mov')):
            time.sleep(10)

        # Step 2: publicar
        publish_res = requests.post(
            f'https://graph.instagram.com/v21.0/{user_id}/media_publish',
            data={
                'creation_id': container_id,
                'access_token': token
            }
        )
        publish_json = publish_res.json()

        if 'id' in publish_json:
            return {'success': True, 'post_id': publish_json['id']}
        else:
            return {'success': False, 'error': str(publish_json.get('error', {}).get('message', 'Erro ao publicar'))}

    except Exception as e:
        return {'success': False, 'error': str(e)}

def check_scheduled_posts():
    now = datetime.now()
    for post in scheduled_posts:
        if post['status'] == 'pending' and post['schedule_time']:
            try:
                scheduled_time = datetime.fromisoformat(post['schedule_time'])
                if now >= scheduled_time:
                    result = publish_to_instagram(
                        post['media_url'],
                        post['caption'],
                        post['post_type']
                    )
                    post['status'] = 'published' if result['success'] else 'error'
            except:
                pass

def run_scheduler():
    schedule.every(1).minutes.do(check_scheduled_posts)
    while True:
        schedule.run_pending()
        time.sleep(30)

# Iniciar scheduler em background
scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
