package main

import (
	"bufio"
	"fmt"
	"io"
	"net"
	"os"
	"strings"
)

func main() {
	if len(os.Args) != 4 {
		fmt.Println("Usage: client.exe <server_host> <server_port> <filename>")
		os.Exit(1)
	}

	serverHost := os.Args[1]
	serverPort := os.Args[2]
	filename := os.Args[3]

	conn, err := net.Dial("tcp", serverHost+":"+serverPort)
	if err != nil {
		fmt.Println("Error while connecting to server:", err)
		os.Exit(1)
	}
	defer func(conn net.Conn) {
		err := conn.Close()
		if err != nil {
			fmt.Println("Error while closing TCP socket:", err)
			os.Exit(1)
		}
	}(conn)

	reader := bufio.NewReader(conn)
	newPortStr, err := reader.ReadString('\n')
	if err != nil {
		fmt.Println("Error while reading new port:", err)
		os.Exit(1)
	}
	newPort := strings.TrimSpace(newPortStr)
	newConn, err := net.Dial("tcp", serverHost+":"+newPort)
	if err != nil {
		fmt.Println("Error while connecting to a new TCP server:", err)
		os.Exit(1)
	}
	defer func(newConn net.Conn) {
		err := newConn.Close()
		if err != nil {
			fmt.Println("Error while closing new TCP socket:", err)
			os.Exit(1)
		}
	}(newConn)

	fmt.Println("Connected to port", newPort)

	request := fmt.Sprintf("GET /%s HTTP/1.1\r\nHost: %s\r\n\r\n", filename, serverHost)
	_, err = newConn.Write([]byte(request))
	if err != nil {
		fmt.Println("Error while sending request:", err)
		os.Exit(1)
	}

	response, err := io.ReadAll(newConn)
	if err != nil {
		fmt.Println("Error while reading response:", err)
		os.Exit(1)
	}
	fmt.Println(string(response))
}
