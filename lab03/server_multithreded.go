package main

import (
	"fmt"
	"net"
	"os"
	"strconv"
	"sync"
)

var portCounter = 9005
var mu sync.Mutex

func main() {
	if len(os.Args) != 2 {
		fmt.Println("Usage: server.exe <port> <concurrency_level>")
		os.Exit(1)
	}

	port := os.Args[1]
	concurrencyLevel, err := strconv.Atoi(os.Args[2])
	if err != nil {
		fmt.Println("concurrency_level must be an integer")
		os.Exit(1)
	}

	sem := make(chan struct{}, concurrencyLevel)

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

		handleInitialConnection(conn, sem)
	}
}

func handleInitialConnection(conn net.Conn, sem chan struct{}) {
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
	go startNewServer(newPort, ready, sem)
	<-ready
	fmt.Println("Sending port:", newPort)
	_, err := fmt.Fprintf(conn, "%d\n", newPort)
	if err != nil {
		fmt.Println("Could not send port")
		return
	}
}

func startNewServer(port int, ready chan struct{}, sem chan struct{}) {
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

	sem <- struct{}{}

	go func() {
		defer func() {
			<-sem
			err := conn.Close()
			if err != nil {
				fmt.Println("Error while closing connection:", err)
				os.Exit(1)
			}
		}()
		handleConnection(conn)
	}()
}
