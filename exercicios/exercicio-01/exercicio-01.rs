use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;

const BUFFER_SIZE: usize = 5;

struct Buffer {
    items: Vec<i32>,
    capacity: usize,
}

impl Buffer {
    fn new(capacity: usize) -> Self {
        Buffer {
            items: Vec::with_capacity(capacity),
            capacity,
        }
    }

    fn is_full(&self) -> bool {
        self.items.len() >= self.capacity
    }

    fn is_empty(&self) -> bool {
        self.items.is_empty()
    }

    fn add(&mut self, item: i32) {
        if !self.is_full() {
            self.items.push(item);
            println!("Produzido: {} | Buffer: {:?}", item, self.items);
        }
    }

    fn remove(&mut self) -> Option<i32> {
        if !self.is_empty() {
            let item = self.items.remove(0);
            println!("Consumido: {} | Buffer: {:?}", item, self.items);
            Some(item)
        } else {
            None
        }
    }
}

fn main() {
    let buffer = Arc::new(Mutex::new(Buffer::new(BUFFER_SIZE)));
    let buffer_producer = Arc::clone(&buffer);
    let buffer_consumer = Arc::clone(&buffer);

    // Thread produtora
    let producer = thread::spawn(move || {
        for i in 1..=10 {
            let mut buf = buffer_producer.lock().unwrap();

            // Espera se o buffer estiver cheio
            while buf.is_full() {
                drop(buf);
                thread::sleep(Duration::from_millis(10));
                buf = buffer_producer.lock().unwrap();
            }

            buf.add(i);
            drop(buf);
            thread::sleep(Duration::from_millis(100));
        }
    });

    // Thread consumidora
    let consumer = thread::spawn(move || {
        for _ in 0..10 {
            let mut buf = buffer_consumer.lock().unwrap();

            // Espera se o buffer estiver vazio
            while buf.is_empty() {
                drop(buf);
                thread::sleep(Duration::from_millis(10));
                buf = buffer_consumer.lock().unwrap();
            }

            buf.remove();
            drop(buf);
            thread::sleep(Duration::from_millis(150));
        }
    });

    producer.join().unwrap();
    consumer.join().unwrap();

    println!("\nProcesso finalizado!");
}