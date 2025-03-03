package main

import (
	"bufio"
	"fmt"
	"net"
	"os"
	"strings"
)

func main() {
	if len(os.Args) != 2 {
		fmt.Println("Usage: server.exe <port>")
		os.Exit(1)
	}

	port := os.Args[1]

	listener, err := net.Listen("tcp", ":"+port)
	if err != nil {
		fmt.Println("Error listening:", err)
		os.Exit(1)
	}
	defer func(listener net.Listener) {
		err := listener.Close()
		if err != nil {
			fmt.Println("Error while closing TCP socket:", err)
			os.Exit(1)
		}
	}(listener)

	fmt.Println("Server started on port:", port)

	for {
		conn, err := listener.Accept()
		if err != nil {
			fmt.Println("Error accepting connection:", err)
			continue
		}

		handleConnection(conn)
	}
}

func handleConnection(conn net.Conn) {
	defer func(conn net.Conn) {
		err := conn.Close()
		if err != nil {
			fmt.Println("Error while closing connection:", err)
			os.Exit(1)
		}
	}(conn)

	reader := bufio.NewReader(conn)
	requestLine, err := reader.ReadString('\n')
	if err != nil {
		if err.Error() == "EOF" {
			return
		}
		fmt.Println("Error reading request:", err)
		return
	}

	parts := strings.Fields(requestLine)
	if len(parts) != 3 {
		fmt.Println("Invalid request line:", requestLine)
		return
	}

	method := parts[0]
	path := parts[1]

	if method != "GET" {
		sendResponse(conn, "405 Method Not Allowed", "text/plain", "Method Not Allowed")
		return
	}

	filePath := "." + path

	content, err := os.ReadFile(filePath)
	if err != nil {
		sendResponse(conn, "404 Not Found", "text/plain", "File Not Found")
		return
	}

	contentType := getContentType(filePath)
	sendResponse(conn, "200 OK", contentType, string(content))
}

func getContentType(filePath string) string {
	switch {
	case strings.HasSuffix(filePath, ".html"):
		return "text/html"
	case strings.HasSuffix(filePath, ".css"):
		return "text/css"
	case strings.HasSuffix(filePath, ".js"):
		return "application/javascript"
	case strings.HasSuffix(filePath, ".json"):
		return "application/json"
	case strings.HasSuffix(filePath, ".png"):
		return "image/png"
	case strings.HasSuffix(filePath, ".jpg") || strings.HasSuffix(filePath, ".jpeg"):
		return "image/jpeg"
	default:
		return "text/plain"
	}
}

func sendResponse(conn net.Conn, status string, contentType string, body string) {
	response := fmt.Sprintf("HTTP/1.1 %s\r\n", status)
	response += fmt.Sprintf("Content-Type: %s\r\n", contentType)
	response += fmt.Sprintf("Content-Length: %d\r\n", len(body))
	response += "\r\n"
	response += body

	_, err := conn.Write([]byte(response))
	if err != nil {
		fmt.Println("Error sending response:", err)
	}
}
