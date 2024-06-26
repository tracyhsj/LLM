
# ----------------------------- #
# SCRIPT FOR BERT MODEL SETUP   #
# AUTHOR: XIAOYANG SONG         #
# ----------------------------- #
import torch
from torch.nn import functional as F
import numpy as np
from icecream import ic
# HuggingFace & Torch
from transformers import AutoTokenizer, BertModel, BertTokenizer, \
    BertForMaskedLM, AutoTokenizer, BertForNextSentencePrediction, \
    BertForQuestionAnswering, OpenAIGPTTokenizer, GPT2LMHeadModel, GPT2Tokenizer, OpenAIGPTLMHeadModel, pipeline, BertForMultipleChoice, \
    BertLMHeadModel, RobertaForCausalLM, AutoConfig

# https://huggingface.co/transformers/v2.4.0/pretrained_models.html
MODEL = {
    'BERT': BertLMHeadModel,
    'RoBERTa': RobertaForCausalLM,
    'SpanBERT': None,
    'GPT': OpenAIGPTLMHeadModel,
    'GPT2': GPT2LMHeadModel}
TOKENIZER = {'BERT': AutoTokenizer,
             'RoBERTa': AutoTokenizer,
             'GPT': OpenAIGPTTokenizer,
             'GPT2': GPT2Tokenizer}


def logit_to_prob(logit, ids):
    # logits: L x Vocab_Size
    # ic(logit.shape)
    # ic(ids.shape)
    assert logit.shape[0] == ids.shape[0]
    prob = torch.softmax(logit, dim=-1)
    return prob[np.arange(ids.shape[0]), ids]


def prob_to_ll(prob, ll_type):
    if ll_type == 'ans_inv_perp':
        return torch.mean(torch.log(prob))
    elif ll_type == 'sent_inv_perp':
        return torch.mean(torch.log(prob))
    else:
        assert False, 'Unrecognized input argument.'


class PROBS():
    def __init__(self, family, model, tokenizer, ll_type):
        self.family = family
        self.model, self.tokenizer = model, tokenizer
        self.ll_type = ll_type

    def __call__(self, prompt, choice):
        tokens = self.tokenizer(prompt + choice, return_tensors="pt")
        ans_token = self.tokenizer(choice, return_tensors="pt")
        if self.family in ['BERT', 'RoBERTa']:
            # FOR BERT family model: trim [CLS] & [SEP] tokens
            answer_input_ids = ans_token.input_ids[0][1:-1]
            length_ans = len(answer_input_ids)
            sent_input_ids = tokens.input_ids[0]
            logit = self.model(**tokens).logits
            prob = logit_to_prob(
                logit.squeeze(), sent_input_ids)[-length_ans-1:-1]
            ll = prob_to_ll(prob, self.ll_type)
            toi = sent_input_ids[-length_ans-1:-1]
            return prob, ll, toi
        elif self.family in ['GPT', 'GPT2']:
            answer_input_ids = ans_token.input_ids[0]
            length_ans = len(answer_input_ids)
            sent_input_ids = tokens.input_ids[0]
            logit = self.model(**tokens).logits
            prob = logit_to_prob(
                logit.squeeze(), sent_input_ids)[-length_ans+1:]
            # ic(prob)
            ll = prob_to_ll(prob, self.ll_type)
            toi = sent_input_ids[-length_ans+1:]
            return prob, ll, toi
        else:
            assert False, 'Unrecognized model family'
