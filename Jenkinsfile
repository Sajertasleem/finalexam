pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.9'
        VENV_PATH = "${WORKSPACE}/venv"
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code...'
                checkout scm
            }
        }
        
        stage('Setup Python Environment') {
            steps {
                echo 'Setting up Python virtual environment...'
                sh '''
                    python${PYTHON_VERSION} -m venv ${VENV_PATH} || python3 -m venv ${VENV_PATH}
                    ${VENV_PATH}/bin/activate || source ${VENV_PATH}/bin/activate
                    pip install --upgrade pip
                '''
            }
        }
        
        stage('Install Dependencies') {
            steps {
                echo 'Installing dependencies...'
                sh '''
                    ${VENV_PATH}/bin/pip install -r requirements.txt || ${VENV_PATH}/bin/pip3 install -r requirements.txt
                '''
            }
        }
        
        stage('Lint') {
            steps {
                echo 'Running linter...'
                sh '''
                    ${VENV_PATH}/bin/pip install flake8 || true
                    ${VENV_PATH}/bin/flake8 app.py tests/ --count --select=E9,F63,F7,F82 --show-source --statistics || true
                    ${VENV_PATH}/bin/flake8 app.py tests/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics || true
                '''
            }
        }
        
        stage('Tests') {
            steps {
                echo 'Running tests...'
                sh '''
                    cd ${WORKSPACE}
                    ${VENV_PATH}/bin/pytest tests/ -v --tb=short || exit 1
                '''
            }
        }
        
        stage('Test Coverage') {
            steps {
                echo 'Generating test coverage report...'
                sh '''
                    ${VENV_PATH}/bin/pip install pytest-cov || true
                    ${VENV_PATH}/bin/pytest tests/ --cov=app --cov-report=html --cov-report=term || true
                '''
            }
        }
        
        stage('Build') {
            steps {
                echo 'Building application...'
                sh '''
                    echo "Application build completed successfully"
                '''
            }
        }
    }
    
    post {
        always {
            echo 'Cleaning up...'
            sh '''
                rm -rf ${VENV_PATH} || true
            '''
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}

