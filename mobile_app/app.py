"""
Mobile app - thin wrapper around the same backend as desktop app.
Runs on port 5001 to allow desktop (5000) and mobile to run simultaneously.
"""
import os
import sys
from flask import Flask, render_template, request, jsonify, redirect, url_for

# Add project root to path
sys.path.insert(0, '/workspace/project/polkiuy1')
from mobile_app.data_store import load_all_projects, load_project, save_project

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(32).hex())

# Load persisted projects on startup
projects = load_all_projects()


def persist_project(project_id: str):
    """Helper to save project to disk after modification."""
    if project_id in projects:
        save_project(project_id, projects[project_id])


# ========================================
# Mobile Screens
# ========================================

@app.route('/')
def home():
    """Mobile Home: Simple vertical list of projects."""
    return render_template('mobile_home.html', projects=projects)


@app.route('/new', methods=['GET', 'POST'])
def new_idea():
    """Mobile New Idea: Simple text area with Analyze button."""
    if request.method == 'POST':
        idea_text = request.json.get('idea_text', '') if request.is_json else request.form.get('idea_text', '')
        if idea_text:
            # Forward to desktop backend
            import requests
            try:
                resp = requests.post('http://localhost:5000/analyze-idea', 
                                   json={'idea_text': idea_text}, timeout=120)
                if resp.status_code == 200:
                    data = resp.json()
                    project_id = data.get('project_id')
                    # Reload to get persisted data
                    projects.update(load_all_projects())
                    return jsonify({'project_id': project_id, 'questions': data.get('questions', [])})
                else:
                    return jsonify({'error': 'Backend error'}), 500
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        return jsonify({'error': 'Idea text required'}), 400
    return render_template('mobile_new_idea.html')


@app.route('/project/<project_id>')
def project_status(project_id):
    """Mobile Project Status: Read-only summary with phase stepper."""
    project = projects.get(project_id)
    if not project:
        # Try to load from disk
        disk_project = load_project(project_id)
        if disk_project:
            projects[project_id] = disk_project
            project = disk_project
    
    if not project:
        return redirect('/')
    
    # Get latest activity from disk if needed
    latest = load_project(project_id)
    if latest and latest.get('activity') != project.get('activity'):
        projects[project_id] = latest
        project = latest
    
    return render_template('mobile_project.html', project=project)


@app.route('/project/<project_id>/questions')
def questions(project_id):
    """Mobile Clarifying Questions: One per screen with swipe."""
    project = projects.get(project_id)
    if not project:
        disk_project = load_project(project_id)
        if disk_project:
            projects[project_id] = disk_project
            project = disk_project
    
    if not project:
        return redirect('/')
    
    return render_template('mobile_questions.html', project=project)


@app.route('/project/<project_id>/answer', methods=['POST'])
def submit_answer(project_id):
    """Submit answer to backend and persist."""
    # Forward to desktop backend
    import requests
    try:
        resp = requests.post(f'http://localhost:5000/project/{project_id}/answer',
                            json=request.json, timeout=10)
        if resp.status_code == 200:
            # Reload from disk to get persisted data
            latest = load_project(project_id)
            if latest:
                projects[project_id] = latest
            return jsonify(resp.json())
        else:
            return jsonify({'error': 'Backend error'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/project/<project_id>/refresh')
def refresh_project(project_id):
    """Refresh project data from disk."""
    latest = load_project(project_id)
    if latest:
        projects[project_id] = latest
        return jsonify(latest)
    return jsonify({'error': 'Not found'}), 404


@app.route('/settings')
def settings():
    """Mobile Settings: Notification toggles only."""
    return render_template('mobile_settings.html')


if __name__ == '__main__':
    print("Mobile app starting on port 5001...")
    print("Make sure desktop app is running on port 5000")
    app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)
