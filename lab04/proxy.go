package main

import (
	"bufio"
	"bytes"
	"crypto/md5"
	"encoding/hex"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
)

type CacheEntry struct {
	LastModified string
	ETag         string
	FilePath     string
}

var cache = make(map[string]CacheEntry)

const cacheDir = "./cache"

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

var blacklist []string

func loadBlackList(filename string) error {
	file, err := os.Open(filename)
	if err != nil {
		return err
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line != "" {
			blacklist = append(blacklist, line)
		}
	}
	return scanner.Err()
}

func isBlocked(url string) bool {
	for _, blocked := range blacklist {
		if strings.HasPrefix(url, blocked) || strings.Contains(url, blocked) {
			return true
		}
	}
	return false
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

func getCacheFilePath(url string) string {
	hash := md5.Sum([]byte(url))
	hashStr := hex.EncodeToString(hash[:])
	return filepath.Join(cacheDir, hashStr)
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

	if isBlocked(targetURL) {
		writer.WriteHeader(http.StatusForbidden)
		io.WriteString(writer, "Access to this page is blocked by the proxy server.")
		log.Printf("Blocked access to %s", targetURL)
		return
	}

	if entry, ok := cache[targetURL]; ok {
		req, err := http.NewRequest("GET", targetURL, nil)
		if err != nil {
			http.Error(writer, "Bad Request", http.StatusBadRequest)
			return
		}
		if entry.LastModified != "" {
			req.Header.Set("If-Modified-Since", entry.LastModified)
		}
		if entry.ETag != "" {
			req.Header.Set("If-None-Match", entry.ETag)
		}
		copyHeader(req.Header, request.Header)
		removeHopByHopHeaders(req.Header)

		client := &http.Client{}
		resp, err := client.Do(req)
		if err != nil {
			http.Error(writer, "Error forwarding request", http.StatusInternalServerError)
			return
		}
		defer resp.Body.Close()

		if resp.StatusCode == http.StatusNotModified {
			// object not changed, get from cache
			file, err := os.Open(entry.FilePath)
			if err != nil {
				http.Error(writer, "Error reading cache", http.StatusInternalServerError)
				return
			}
			defer file.Close()
			_, err = io.Copy(writer, file)
			if err != nil {
				log.Printf("Error copying cache to response: %v", err)
			}
			log.Printf("Served from cache: %s", targetURL)
			return
		} else if resp.StatusCode == http.StatusOK {
			// object changed, update cache
			cacheFilePath := getCacheFilePath(targetURL)
			cacheFile, err := os.Create(cacheFilePath)
			if err != nil {
				http.Error(writer, "Error creating cache file", http.StatusInternalServerError)
				return
			}
			defer cacheFile.Close()
			_, err = io.Copy(cacheFile, resp.Body)
			if err != nil {
				log.Printf("Error writing to cache: %v", err)
			}
			lastModified := resp.Header.Get("Last-Modified")
			etag := resp.Header.Get("ETag")
			cache[targetURL] = CacheEntry{
				LastModified: lastModified,
				ETag:         etag,
				FilePath:     cacheFilePath,
			}
			copyHeader(writer.Header(), resp.Header)
			removeHopByHopHeaders(writer.Header())
			writer.WriteHeader(resp.StatusCode)
			_, err = io.Copy(writer, resp.Body)
			if err != nil {
				log.Printf("Error copying response body: %v", err)
			}
			log.Printf("Updated cache and served: %s", targetURL)
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

	cacheFilePath := getCacheFilePath(targetURL)
	cacheFile, err := os.Create(cacheFilePath)
	if err != nil {
		http.Error(writer, "Error creating cache file", http.StatusInternalServerError)
		return
	}
	defer cacheFile.Close()
	_, err = io.Copy(cacheFile, resp.Body)
	if err != nil {
		log.Printf("Error writing to cache: %v", err)
	}

	lastModified := resp.Header.Get("Last-Modified")
	etag := resp.Header.Get("ETag")
	cache[targetURL] = CacheEntry{
		LastModified: lastModified,
		ETag:         etag,
		FilePath:     cacheFilePath,
	}

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
	err = loadBlackList("blackList.txt")
	if err != nil {
		log.Fatal("Error while loading blackList:", err.Error())
		return
	}

	http.HandleFunc("/", handler)
	log.Fatal(http.ListenAndServe(":8888", nil))
}
