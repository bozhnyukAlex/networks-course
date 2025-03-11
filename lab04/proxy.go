package main

import (
	"bytes"
	"io"
	"log"
	"net/http"
	"os"
	"strings"
)

func copyHeader(dst, src http.Header) {
	for k, vv := range src {
		for _, v := range vv {
			dst.Add(k, v)
		}
	}
}

var hopByHopHeaders = []string{
	"Connection",
	"Keep-Alive",
	"Proxy-Authenticate",
	"Proxy-Authorization",
	"TE",
	"Trailers",
	"Transfer-Encoding",
	"Upgrade",
}

func removeHopByHopHeaders(header http.Header) {
	for _, h := range hopByHopHeaders {
		header.Del(h)
	}
}

func parseTargetURL(path string) (string, error) {
	if strings.HasPrefix(path, "/") {
		path = path[1:]
	}
	parts := strings.SplitN(path, "/", 2)
	host := parts[0]
	var targetPath string
	if len(parts) > 1 {
		targetPath = "/" + parts[1]
	} else {
		targetPath = "/"
	}
	targetURL := "http://" + host + targetPath
	return targetURL, nil
}

func handler(writer http.ResponseWriter, request *http.Request) {
	if request.Method != "GET" && request.Method != "POST" {
		http.Error(writer, "Only GET and POST methods are supported", http.StatusMethodNotAllowed)
		return
	}

	var targetURL string
	if request.URL.Host != "" {
		targetURL = request.URL.String()
	} else {
		var err error
		targetURL, err = parseTargetURL(request.URL.Path)
		if err != nil {
			http.Error(writer, "Bad Request", http.StatusBadRequest)
			return
		}
	}

	var body io.Reader
	if request.Method == "POST" {
		bodyData, err := io.ReadAll(request.Body)
		if err != nil {
			http.Error(writer, "Error reading request body", http.StatusBadRequest)
			return
		}
		body = bytes.NewReader(bodyData)
	}

	newReq, err := http.NewRequest(request.Method, targetURL, body)
	if err != nil {
		http.Error(writer, "Bad Request", http.StatusBadRequest)
		return
	}

	copyHeader(newReq.Header, request.Header)
	removeHopByHopHeaders(newReq.Header)

	client := &http.Client{
		CheckRedirect: func(req *http.Request, via []*http.Request) error {
			return http.ErrUseLastResponse
		},
	}

	resp, err := client.Do(newReq)
	if err != nil {
		http.Error(writer, "Error forwarding request", http.StatusInternalServerError)
		return
	}
	defer resp.Body.Close()

	copyHeader(writer.Header(), resp.Header)
	removeHopByHopHeaders(writer.Header())

	writer.WriteHeader(resp.StatusCode)
	if resp.ContentLength != 0 && resp.StatusCode != 204 && resp.StatusCode != 304 {
		_, err = io.Copy(writer, resp.Body)
		if err != nil {
			log.Printf("Error copying response body: %v", err)
			return
		}
	}

	log.Printf("Proxied %s request to %s, status code: %d", request.Method, targetURL, resp.StatusCode)
}

func main() {
	logFile, err := os.OpenFile("proxy.log", os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
	if err != nil {
		log.Fatal("Cannot open log file:", err)
	}
	log.SetOutput(logFile)

	http.HandleFunc("/", handler)
	log.Fatal(http.ListenAndServe(":8888", nil))
}
