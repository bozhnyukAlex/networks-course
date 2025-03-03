package main

import (
	"fmt"
	"net"
	"os"
	"sync"
)

var portCounter = 9005
var mu sync.Mutex

func main() {
	if len(os.Args) != 2 {
		fmt.Println("Usage: server.exe <port>")
		os.Exit(1)
	}

	port := os.Args[1]
	listener, err := net.Listen("tcp", ":"+port)
	if err != nil {
		fmt.Println("Error while running server:", err)
		os.Exit(1)
	}
	defer func(listener net.Listener) {
		err := listener.Close()
		if err != nil {
			fmt.Println("Error while closing TCP socket:", err)
			os.Exit(1)
		}
	}(listener)

	fmt.Println("Main server runs on port", port)
	for {
		conn, err := listener.Accept()
		if err != nil {
			fmt.Println("Error accepting connection:", err)
			continue
		}

		handleInitialConnection(conn)
	}
}

func handleInitialConnection(conn net.Conn) {
	defer func(conn net.Conn) {
		err := conn.Close()
		if err != nil {
			fmt.Println("Error while closing initial connection:", err)
			return
		}
	}(conn)

	mu.Lock()
	newPort := portCounter
	portCounter = portCounter + 1
	mu.Unlock()

	ready := make(chan struct{})
	go startNewServer(newPort, ready)
	<-ready
	fmt.Println("Sending port:", newPort)
	_, err := fmt.Fprintf(conn, "%d\n", newPort)
	if err != nil {
		fmt.Println("Could not send port")
		return
	}
}

func startNewServer(port int, ready chan struct{}) {
	listener, err := net.Listen("tcp", fmt.Sprintf(":%d", port))
	if err != nil {
		fmt.Println("Error starting server on port", port, ":", err)
		return
	}

	defer func(listener net.Listener) {
		err := listener.Close()
		if err != nil {
			fmt.Println("Error closing server")
		}
	}(listener)

	fmt.Println("New server is running on port", port)

	close(ready)

	conn, err := listener.Accept()
	if err != nil {
		fmt.Println("Error while accepting connection", port, ":", err)
		return
	}
	go handleConnection(conn)
}
