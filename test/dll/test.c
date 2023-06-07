#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct node {
    char a[0x10];
    struct node* next;
};

void append(struct node** head_ref, char* new_data) {
    struct node* new_node = (struct node*)malloc(sizeof(struct node));
    strcpy(new_node->a, new_data);
    new_node->next = NULL;
    if (*head_ref == NULL) {
        *head_ref = new_node;
        return;
    }
    struct node* last = *head_ref;
    while (last->next != NULL) {
        last = last->next;
    }
    last->next = new_node;
}

void delete(struct node** head_ref, char* key) {
    struct node* temp = *head_ref, *prev;
    if (temp != NULL && strcmp(temp->a, key) == 0) {
        *head_ref = temp->next;
        free(temp);
        return;
    }
    while (temp != NULL && strcmp(temp->a, key) != 0) {
        prev = temp;
        temp = temp->next;
    }
    if (temp == NULL) {
        return;
    }
    prev->next = temp->next;
    free(temp);
}

void print_list(struct node* node) {
    while (node != NULL) {
        printf("%s -> ", node->a);
        node = node->next;
    }
    printf("NULL\n");
}

int main() {
    struct node* head = NULL;
    append(&head, "apple");
    append(&head, "banana");
    append(&head, "cherry");
    print_list(head);
    delete(&head, "banana");
    print_list(head);
    return 0;
}
