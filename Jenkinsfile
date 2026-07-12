pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        IMAGE_NAME  = "sensor-api"
        IMAGE_TAG   = "${env.BUILD_NUMBER}"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
                sh 'mkdir -p reports'
            }
        }

        stage('Build & Unit Test') {
            steps {
                sh '''
                    cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
                    cmake --build build -j "$(nproc)"
                    ctest --test-dir build --output-on-failure
                '''
            }
        }

        stage('SAST - Static Analysis') {
            when { not { branch 'feature/*' } }
            steps {
                sh '''
                    cppcheck --enable=all --inconclusive --std=c++17 \
                        --xml --xml-version=2 src/ 2> reports/cppcheck.xml || true
                '''
            }
        }

        stage('OWASP Dependency Check') {
            when { not { branch 'feature/*' } }
            steps {
                dependencyCheck additionalArguments: '--scan ./ --format XML --out reports/',
                                odcInstallation: 'OWASP-DC'
                dependencyCheckPublisher pattern: 'reports/dependency-check-report.xml'
            }
        }

        stage('Secrets Scan') {
            when { not { branch 'feature/*' } }
            steps {
                sh '''
                    docker run --rm \
                        --volumes-from jenkins \
                        zricethezav/gitleaks:latest detect \
                        --source=$WORKSPACE --no-git \
                        --report-format=json \
                        --report-path=$WORKSPACE/reports/gitleaks.json || true
                '''
            }
        }

        stage('Build Container Image') {
            when { anyOf { branch 'main'; branch 'develop' } }
            steps {
                sh 'docker build -t $IMAGE_NAME:$IMAGE_TAG .'
            }
        }

        stage('SBOM Generation') {
            when { anyOf { branch 'main'; branch 'develop' } }
            steps {
                sh '''
                    docker run --rm \
                        --volumes-from jenkins \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        anchore/syft:latest $IMAGE_NAME:$IMAGE_TAG \
                        -o cyclonedx-json=$WORKSPACE/reports/sbom.cyclonedx.json \
                        -o spdx-json=$WORKSPACE/reports/sbom.spdx.json
                '''
            }
        }

        stage('SCA - Image Vulnerability Scan') {
            when { anyOf { branch 'main'; branch 'develop' } }
            steps {
                sh '''
                    docker run --rm \
                        --volumes-from jenkins \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        aquasec/trivy:latest image \
                        --format json --output $WORKSPACE/reports/trivy.json \
                        --severity HIGH,CRITICAL \
                        $IMAGE_NAME:$IMAGE_TAG || true
                '''
            }
        }

        stage('Security Quality Gate') {
            when { anyOf { branch 'main'; branch 'develop' } }
            steps {
                sh 'python3 scripts/security_report.py reports/'
            }
        }

        stage('Push to Docker Hub') {
            when { branch 'main' }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-credentials',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                        echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                        docker tag $IMAGE_NAME:$IMAGE_TAG $DOCKER_USER/$IMAGE_NAME:$IMAGE_TAG
                        docker tag $IMAGE_NAME:$IMAGE_TAG $DOCKER_USER/$IMAGE_NAME:latest
                        docker push $DOCKER_USER/$IMAGE_NAME:$IMAGE_TAG
                        docker push $DOCKER_USER/$IMAGE_NAME:latest
                    '''
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
        }
        success {
            echo "Pipeline passed on branch: ${env.BRANCH_NAME}"
        }
        failure {
            echo "Pipeline failed on branch: ${env.BRANCH_NAME} -- check logs above."
        }
    }
}
