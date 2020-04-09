podTemplate(yaml: '''
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: docker
    image: docker:19.03.8
    command:
    - sleep
    args:
    - 99d
    env:
      - name: DOCKER_HOST
        value: tcp://localhost:2375
  - name: docker-daemon
    image: docker:19.03.8-dind
    securityContext:
      privileged: true
    env:
      - name: DOCKER_TLS_CERTDIR
        value: ""
''') {
    node(POD_LABEL) {
        def colabot
        git 'https://github.com/ciscops/colabot-alert.git'
        container('docker') {
            stage('Clone repository') {
                checkout scm
            }
            stage('Build image') {
                colabot = docker.build("stmosher/colabot-alert")
            }
//             stage('Test image') {
//                 colabot.inside {
//                     sh 'node --version'
//                 }
//             }
            stage('Push image') {
                docker.withRegistry('https://registry.hub.docker.com', 'dockerhub') {
                    colabot.push("${env.BUILD_NUMBER}")
                    colabot.push("latest")
                }
            }             
        }
    }
}