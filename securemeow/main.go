package main

import (
	"context"
	"fmt"
	"io/ioutil"
	"net/http"
	"time"
)

var explicitWait bool

var deadline = time.Second * 120

func scan(in chan string) {
	var input string
	_, err := fmt.Scanln(&input)
	if err != nil {
		fmt.Println(err)
	}

	in <- input
}

func main() {
	http.HandleFunc("/explicit", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}

		if explicitWait {
			w.WriteHeader(http.StatusBadRequest)
			w.Write([]byte("Another request is already in progress"))
			return
		}

		explicitWait = true

		bodyB, err := ioutil.ReadAll(r.Body)

		if err != nil {
			w.WriteHeader(http.StatusBadRequest)
			return
		}

		body := string(bodyB)

		fmt.Print("Explicit action:", body, "\n\nAllow [Y/N]: ")

		var allow string

		ctx, cancel := context.WithTimeout(context.Background(), deadline)

		defer cancel()

		c := make(chan string, 1)
		go scan(c)

		select {
		case <-ctx.Done():
			// didnt type for deadline seconds
			w.WriteHeader(http.StatusForbidden)
			w.Write([]byte("Timed out"))
			fmt.Println("Timed out")
			explicitWait = false
			return
		case allow = <-c:
			if allow == "Y" {
				w.WriteHeader(http.StatusOK)
				w.Write([]byte("OK"))
			} else {
				w.WriteHeader(http.StatusForbidden)
				w.Write([]byte("Forbidden"))
			}
		}

		explicitWait = false
	})

	http.ListenAndServe(":9110", nil)
}
