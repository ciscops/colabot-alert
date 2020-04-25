podTemplate(
  namespace: "default",
  serviceAccount: "colabot-build",
  yaml: '''
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
  - name: kubectl
    image: stmosher/kubectl
    command: ["sleep"]
    args: ["100000"]
''') {
    node(POD_LABEL) {
        container('docker') {
            stage('Clone repository') {
                checkout scm
            }
            stage('Build container') {
                colabot = docker.build("stmosher/colabot-alert")
            }
            stage('Push container to docker hub ') {
                docker.withRegistry('https://registry.hub.docker.com', 'dockerhub') {
                    colabot.push("${env.BUILD_NUMBER}")
                    colabot.push("latest")
                }
            }
        }
        container("kubectl") {
            stage('Clone k8s manifest') {
                sh "apk update"
                sh "apk upgrade"
                sh "apk add git"
                sh 'git config --global credential.helper cache'
                withCredentials([usernamePassword(credentialsId: 'github', passwordVariable: 'pass', usernameVariable: 'user')]) {
                    sh 'git clone https://"$user":"$pass"@github.com/ciscops/colabot-private.git'
		    }
            stage('Deploy new COLABot-alert to K8s cluster') {
                try {
                    sh "kubectl delete -f colabot-private/colabot_alerts/colabot-alert.yaml"
                } catch(Exception ex) {
                    sh "echo No need to delete"
                }
                sh "kubectl create -f colabot-private/colabot_alerts/colabot-alert.yaml"
                sh 'echo Finished'
            }
        }
    }
}
