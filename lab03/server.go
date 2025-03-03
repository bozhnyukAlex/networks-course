package main

import (
	"fmt"
	"net"
	"os"
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
